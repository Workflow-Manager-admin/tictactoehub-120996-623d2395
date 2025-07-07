from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select
from datetime import datetime
from typing import List, Optional, Dict
from .db import get_session
from .models import Game, Move
from pydantic import BaseModel, Field

# Swagger/OpenAPI tags
openapi_tags = [
    {"name": "games",       "description": "Tic Tac Toe gameplay operations"},
    {"name": "leaderboard", "description": "Leaderboard/statistics"},
    {"name": "history",     "description": "Public game history"},
]

router = APIRouter()

# ---------- Pydantic API Schemas ----------

# No player_id, just anonymous strings for X and O (or leave empty for now)
class GameCreateRequest(BaseModel):
    player_x_name: Optional[str] = Field(default="Player X", description="Label for player X")
    player_o_name: Optional[str] = Field(default="Player O", description="Label for player O")

class GameMoveRequest(BaseModel):
    symbol: str = Field(..., description="'X' or 'O'")
    position: int = Field(..., ge=0, le=8, description="Board position (0-8)")

class GameStatusOut(BaseModel):
    id: int
    board_state: str
    status: str
    current_turn: str
    winner: Optional[str]
    moves: List[Dict]
    player_labels: Dict[str, str]

class LeaderboardEntryOut(BaseModel):
    symbol: str
    wins: int
    losses: int
    draws: int
    total_games: int
    last_played: Optional[datetime]

class GameHistoryEntry(BaseModel):
    game_id: int
    created_at: datetime
    completed_at: Optional[datetime]
    result: Optional[str]

# ---------- GAMEPLAY ROUTES ----------

@router.post("/games/new", tags=["games"], summary="Start new game", description="Create a new public Tic Tac Toe game")
def create_game(data: GameCreateRequest, session: Session = Depends(get_session)):
    new_game = Game(
        player_x_label=data.player_x_name,
        player_o_label=data.player_o_name,
        board_state=" " * 9,
        status="active",
        current_turn="X"
    )
    session.add(new_game)
    session.commit()
    session.refresh(new_game)
    return {"game_id": new_game.id}

@router.post("/games/{game_id}/move", tags=["games"], summary="Make a move", description="Place a move in a public game")
def make_move(game_id: int, data: GameMoveRequest, session: Session = Depends(get_session)):
    game = session.get(Game, game_id)
    if not game:
        raise HTTPException(status_code=404, detail="Game not found")
    if game.status != "active":
        raise HTTPException(status_code=400, detail="Game not active")
    symbol = data.symbol.upper()
    if symbol not in ("X", "O"):
        raise HTTPException(status_code=400, detail="Invalid symbol")
    if symbol != game.current_turn:
        raise HTTPException(status_code=400, detail="Not this player's turn")
    board = list(game.board_state)
    if board[data.position] != " ":
        raise HTTPException(status_code=400, detail="Cell already occupied")
    # Mark the move
    board[data.position] = symbol
    move_order = len([c for c in board if c != " "])
    move = Move(
        game_id=game.id,
        move_order=move_order-1,
        position=data.position,
        symbol=symbol,
    )
    session.add(move)
    game.board_state = "".join(board)
    # Win/draw checks
    winner = check_winner(board)
    if winner:
        game.status = "win"
        game.winner = winner
        game.completed_at = datetime.utcnow()
    elif " " not in board:
        game.status = "draw"
        game.winner = None
        game.completed_at = datetime.utcnow()
    else:
        game.current_turn = "O" if symbol == "X" else "X"
    session.commit()
    return {"success": True, "next_turn": game.current_turn, "status": game.status, "winner": game.winner}

def check_winner(board_l: List[str]) -> Optional[str]:
    lines = [
        [0,1,2],[3,4,5],[6,7,8],  # rows
        [0,3,6],[1,4,7],[2,5,8],  # cols
        [0,4,8],[2,4,6]           # diags
    ]
    for a, b, c in lines:
        if board_l[a] != " " and board_l[a] == board_l[b] == board_l[c]:
            return board_l[a]
    return None

@router.get("/games/{game_id}/status", tags=["games"], summary="Get game status", description="Retrieve board state and status by game ID", response_model=GameStatusOut)
def get_game_status(game_id: int, session: Session = Depends(get_session)):
    game = session.get(Game, game_id)
    if not game:
        raise HTTPException(status_code=404, detail="Game not found")
    moves = session.exec(select(Move).where(Move.game_id == game_id).order_by(Move.move_order)).all()
    return GameStatusOut(
        id=game.id,
        board_state=game.board_state,
        status=game.status,
        current_turn=game.current_turn,
        winner=game.winner,
        moves=[
            {"position": m.position, "order": m.move_order, "symbol": m.symbol} for m in moves
        ],
        player_labels={
            "X": getattr(game, "player_x_label", "X"),
            "O": getattr(game, "player_o_label", "O")
        }
    )

# ---------- LEADERBOARD (PUBLIC, SIMPLE) ----------

@router.get("/leaderboard", tags=["leaderboard"], summary="Get leaderboard", description="Fetch simple stats for X/O games", response_model=List[LeaderboardEntryOut])
def get_leaderboard(session: Session = Depends(get_session)):
    # For simplicity, count global stats for X and O
    leaderboard = {
        "X": {"symbol": "X", "wins": 0, "losses": 0, "draws": 0, "total_games": 0, "last_played": None},
        "O": {"symbol": "O", "wins": 0, "losses": 0, "draws": 0, "total_games": 0, "last_played": None}
    }
    games = session.exec(select(Game)).all()
    for g in games:
        if g.status not in ("win", "draw"):
            continue
        if g.status == "draw":
            leaderboard["X"]["draws"] += 1
            leaderboard["O"]["draws"] += 1
        elif g.winner == "X":
            leaderboard["X"]["wins"] += 1
            leaderboard["O"]["losses"] += 1
        elif g.winner == "O":
            leaderboard["O"]["wins"] += 1
            leaderboard["X"]["losses"] += 1
        leaderboard["X"]["total_games"] += 1
        leaderboard["O"]["total_games"] += 1
        for sym in ("X", "O"):
            if not leaderboard[sym]["last_played"] or (g.completed_at and g.completed_at > leaderboard[sym]["last_played"]):
                leaderboard[sym]["last_played"] = g.completed_at
    return [LeaderboardEntryOut(**leaderboard["X"]), LeaderboardEntryOut(**leaderboard["O"])]

# ---------- GAME HISTORY (PUBLIC, NO USERS) ----------

@router.get("/history", tags=["history"], response_model=List[GameHistoryEntry],
            summary="Game history", description="List public game history and results")
def get_history(session: Session = Depends(get_session)):
    games = session.exec(select(Game)).order_by(Game.completed_at.desc()).all()
    history = []
    for g in games:
        history.append(GameHistoryEntry(
            game_id=g.id,
            created_at=g.created_at,
            completed_at=g.completed_at,
            result=g.status if g.status in ("win", "draw") else "in-progress"
        ))
    return history
