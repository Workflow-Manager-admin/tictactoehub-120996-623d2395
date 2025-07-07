from datetime import datetime
from typing import Optional, List
from sqlmodel import SQLModel, Field, Relationship

# PUBLIC_INTERFACE
class Game(SQLModel, table=True):
    """
    ORM model for a Tic Tac Toe game session (no user, public play).
    """
    id: Optional[int] = Field(default=None, primary_key=True, description="Unique game ID")
    board_state: str = Field(nullable=False, description="Serialized board, e.g., 'XOXOX   O'")
    status: str = Field(nullable=False, description="Game status: active/win/draw/etc")
    current_turn: str = Field(nullable=False, description="'X' or 'O', whose turn it is")
    created_at: datetime = Field(default_factory=datetime.utcnow, nullable=False, description="Game creation time")
    completed_at: Optional[datetime] = Field(default=None, description="Game end timestamp")
    winner: Optional[str] = Field(default=None, description="'X', 'O', or None if draw/in progress")
    player_x_label: Optional[str] = Field(default="Player X", description="Label for player X")
    player_o_label: Optional[str] = Field(default="Player O", description="Label for player O")
    moves: List["Move"] = Relationship(back_populates="game")

# PUBLIC_INTERFACE
class Move(SQLModel, table=True):
    """
    ORM model for a single move made in a Tic Tac Toe game. Player is anonymous/public.
    """
    id: Optional[int] = Field(default=None, primary_key=True, description="Unique move ID")
    game_id: int = Field(foreign_key="game.id", nullable=False, description="Related game")
    move_order: int = Field(nullable=False, description="Order of the move in the game (0-8)")
    position: int = Field(nullable=False, description="Index on board (0-8)")
    symbol: str = Field(nullable=False, description="'X' or 'O'")
    played_at: datetime = Field(default_factory=datetime.utcnow, nullable=False, description="Move timestamp")
    game: Optional[Game] = Relationship(back_populates="moves")

# PUBLIC_INTERFACE
class LeaderboardStat(SQLModel, table=True):
    """
    Only used for migration compatibility—could be deprecated.
    """
    id: Optional[int] = Field(default=None, primary_key=True)
    # No user_id or stats anymore
