from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select
from datetime import datetime
from typing import List, Optional, Dict
from .db import get_session
from .models import User, Game, Move, LeaderboardStat
from pydantic import BaseModel, Field
import hashlib

# Swagger/OpenAPI tags
openapi_tags = [
    {"name": "auth",        "description": "Authentication (register/login)"},
    {"name": "games",       "description": "Tic Tac Toe gameplay operations"},
    {"name": "leaderboard", "description": "Leaderboard/statistics"},
    {"name": "users",       "description": "User profile and game history"},
]

router = APIRouter()

# ------------- UTILITIES -------------

def hash_password(password: str) -> str:
    # For demo only! Use bcrypt or Argon2 in prod!
    return hashlib.sha256(password.encode()).hexdigest()

def verify_password(plain: str, hashed: str) -> bool:
    return hash_password(plain) == hashed

def get_user_by_username(session: Session, username: str) -> Optional[User]:
    return session.exec(select(User).where(User.username == username)).first()

# ---------- Pydantic API Schemas ----------

class RegisterRequest(BaseModel):
    username: str = Field(..., description="Desired username")
    email: str = Field(..., description="User's email address")
    password: str = Field(..., min_length=6, description="Password (min 6 chars)")

class LoginRequest(BaseModel):
    username: str = Field(..., description="Username")
    password: str = Field(..., description="Password")

class UserOut(BaseModel):
    id: int
    username: str
    email: str
    created_at: datetime

class GameCreateRequest(BaseModel):
    player_x_id: int = Field(..., description="User ID for player X")
    player_o_id: int = Field(..., description="User ID for player O")    

class GameMoveRequest(BaseModel):
    player_id: int = Field(..., description="User ID making the move")
    position: int = Field(..., ge=0, le=8, description="Board position (0-8)")

class GameStatusOut(BaseModel):
    id: int
    board_state: str
    status: str
    current_turn: str
    winner: Optional[str]
    moves: List[Dict]
    players: Dict[str, int]

class LeaderboardEntryOut(BaseModel):
    user_id: int
    username: str
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
    as_symbol: str

# ---------- AUTH ROUTES ----------

@router.post("/auth/register", tags=["auth"], summary="Register user", description="Create a new user account")
def register_user(data: RegisterRequest, session: Session = Depends(get_session)):
    existing = session.exec(select(User).where(
        (User.username == data.username) | (User.email == data.email)
    )).first()
    if existing:
        raise HTTPException(status_code=400, detail="Username or email already exists")
    user = User(
        username=data.username,
        email=data.email,
        password_hash=hash_password(data.password)
    )
    session.add(user)
    session.commit()
    session.refresh(user)
    return UserOut.model_validate(user)

@router.post("/auth/login", tags=["auth"], summary="Login", description="Authenticate a user and return user info")
def login_user(data: LoginRequest, session: Session = Depends(get_session)):
    user = get_user_by_username(session, data.username)
    if not user or not verify_password(data.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    return UserOut.model_validate(user)

# ---------- GAMEPLAY ROUTES ----------

@router.post("/games/new", tags=["games"], summary="Start new game", description="Create a new Tic Tac Toe game")
def create_game(data: GameCreateRequest, session: Session = Depends(get_session)):
    if data.player_x_id == data.player_o_id:
        raise HTTPException(status_code=400, detail="Cannot play against yourself")
    # user existence check
    user_x = session.get(User, data.player_x_id)
    user_o = session.get(User, data.player_o_id)
    if not user_x or not user_o:
        raise HTTPException(status_code=404, detail="Player(s) do not exist")
    new_game = Game(
        player_x_id=data.player_x_id,
        player_o_id=data.player_o_id,
        board_state=" " * 9,
        status="active",
        current_turn="X"
    )
    session.add(new_game)
    session.commit()
    session.refresh(new_game)
    return {"game_id": new_game.id}

@router.post("/games/{game_id}/move", tags=["games"], summary="Make a move", description="Place a move in a game")
def make_move(game_id: int, data: GameMoveRequest, session: Session = Depends(get_session)):
    game = session.get(Game, game_id)
    if not game:
        raise HTTPException(status_code=404, detail="Game not found")
    if game.status != "active":
        raise HTTPException(status_code=400, detail="Game not active")
    symbol = "X" if data.player_id == game.player_x_id else "O" if data.player_id == game.player_o_id else None
    if not symbol:
        raise HTTPException(status_code=403, detail="Player not part of this game")
    if (symbol != game.current_turn):
        raise HTTPException(status_code=400, detail="Not this player's turn")
    board = list(game.board_state)
    if board[data.position] != " ":
        raise HTTPException(status_code=400, detail="Cell already occupied")
    # Mark the move
    board[data.position] = symbol
    move_order = len([c for c in board if c != " "])
    move = Move(
        game_id=game.id,
        player_id=data.player_id,
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
        _leaderboard_update(session, winner, game)
    elif " " not in board:
        game.status = "draw"
        game.winner = None
        game.completed_at = datetime.utcnow()
        _leaderboard_update(session, None, game)
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

def _leaderboard_update(session: Session, winner: Optional[str], game: Game):
    # winner: "X"/"O"/None
    for user_id, symbol in [(game.player_x_id, "X"), (game.player_o_id, "O")]:
        entry = session.exec(select(LeaderboardStat).where(LeaderboardStat.user_id == user_id)).first()
        if not entry:
            entry = LeaderboardStat(user_id=user_id)
            session.add(entry)
        if winner == symbol:
            entry.wins += 1
        elif winner is None:
            entry.draws += 1
        else:
            entry.losses += 1
        entry.total_games += 1
        entry.last_played = datetime.utcnow()

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
            {"position": m.position, "order": m.move_order, "symbol": m.symbol, "player_id": m.player_id} for m in moves
        ],
        players={"X": game.player_x_id, "O": game.player_o_id}
    )

# ---------- LEADERBOARD ----------

@router.get("/leaderboard", tags=["leaderboard"], summary="Get leaderboard", description="Fetch stats for all players", response_model=List[LeaderboardEntryOut])
def get_leaderboard(session: Session = Depends(get_session)):
    stats = session.exec(select(LeaderboardStat)).all()
    out = []
    for entry in stats:
        user = session.get(User, entry.user_id)
        out.append(LeaderboardEntryOut(
            user_id=entry.user_id,
            username=user.username if user else "N/A",
            wins=entry.wins,
            losses=entry.losses,
            draws=entry.draws,
            total_games=entry.total_games,
            last_played=entry.last_played
        ))
    out.sort(key=lambda e: (e.wins, -e.losses), reverse=True)
    return out

# ---------- USER HISTORY ----------

@router.get("/users/{user_id}/history", tags=["users"], response_model=List[GameHistoryEntry],
            summary="Get user game history", description="List a user's game history and results")
def get_user_history(user_id: int, session: Session = Depends(get_session)):
    query_x = select(Game).where(Game.player_x_id == user_id)
    query_o = select(Game).where(Game.player_o_id == user_id)
    games_x = session.exec(query_x).all()
    games_o = session.exec(query_o).all()
    history = []
    for g in games_x:
        history.append(GameHistoryEntry(
            game_id=g.id,
            created_at=g.created_at,
            completed_at=g.completed_at,
            result=("win" if g.winner == "X" else "lose" if g.winner == "O" else "draw" if g.status == "draw" else "in-progress"),
            as_symbol="X"
        ))
    for g in games_o:
        history.append(GameHistoryEntry(
            game_id=g.id,
            created_at=g.created_at,
            completed_at=g.completed_at,
            result=("win" if g.winner == "O" else "lose" if g.winner == "X" else "draw" if g.status == "draw" else "in-progress"),
            as_symbol="O"
        ))
    history.sort(key=lambda x: (x.completed_at or datetime.utcnow()), reverse=True)
    return history
