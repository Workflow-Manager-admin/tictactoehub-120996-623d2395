from datetime import datetime
from typing import Optional, List
from sqlmodel import SQLModel, Field, Relationship


# PUBLIC_INTERFACE
class User(SQLModel, table=True):
    """
    ORM model for a user account, for authentication and gameplay.
    """
    id: Optional[int] = Field(default=None, primary_key=True, description="Unique user ID")
    username: str = Field(index=True, unique=True, nullable=False, description="Username chosen by the user")
    email: str = Field(unique=True, nullable=False, description="User email address")
    password_hash: str = Field(nullable=False, description="Hashed user password")
    created_at: datetime = Field(default_factory=datetime.utcnow, nullable=False, description="User creation timestamp")
    is_active: bool = Field(default=True, description="Set to false for disabled/deleted accounts")

    games_as_x: List["Game"] = Relationship(back_populates="player_x", sa_relationship_kwargs={"foreign_keys": "[Game.player_x_id]"})
    games_as_o: List["Game"] = Relationship(back_populates="player_o", sa_relationship_kwargs={"foreign_keys": "[Game.player_o_id]"})
    moves: List["Move"] = Relationship(back_populates="player")
    leaderboard_entry: Optional["LeaderboardStat"] = Relationship(back_populates="user")


# PUBLIC_INTERFACE
class Game(SQLModel, table=True):
    """
    ORM model for a Tic Tac Toe game session.
    """
    id: Optional[int] = Field(default=None, primary_key=True, description="Unique game ID")
    board_state: str = Field(nullable=False, description="Serialized board, e.g., 'XOXOX   O'")
    status: str = Field(nullable=False, description="Game status: active/win/draw/etc")
    current_turn: str = Field(nullable=False, description="'X' or 'O', whose turn it is")
    created_at: datetime = Field(default_factory=datetime.utcnow, nullable=False, description="Game creation time")
    completed_at: Optional[datetime] = Field(default=None, description="Game end timestamp")
    winner: Optional[str] = Field(default=None, description="'X', 'O', or None if draw/in progress")

    # Foreign keys
    player_x_id: int = Field(foreign_key="user.id", nullable=False, description="User ID of 'X' player")
    player_o_id: int = Field(foreign_key="user.id", nullable=False, description="User ID of 'O' player")
    player_x: Optional[User] = Relationship(back_populates="games_as_x", sa_relationship_kwargs={"foreign_keys": "[Game.player_x_id]"})
    player_o: Optional[User] = Relationship(back_populates="games_as_o", sa_relationship_kwargs={"foreign_keys": "[Game.player_o_id]"})

    moves: List["Move"] = Relationship(back_populates="game")


# PUBLIC_INTERFACE
class Move(SQLModel, table=True):
    """
    ORM model for a single move made in a Tic Tac Toe game.
    """
    id: Optional[int] = Field(default=None, primary_key=True, description="Unique move ID")
    game_id: int = Field(foreign_key="game.id", nullable=False, description="Related game")
    player_id: int = Field(foreign_key="user.id", nullable=False, description="User who made the move")
    move_order: int = Field(nullable=False, description="Order of the move in the game (0-8)")
    position: int = Field(nullable=False, description="Index on board (0-8)")
    symbol: str = Field(nullable=False, description="'X' or 'O'")
    played_at: datetime = Field(default_factory=datetime.utcnow, nullable=False, description="Move timestamp")

    game: Optional[Game] = Relationship(back_populates="moves")
    player: Optional[User] = Relationship(back_populates="moves")


# PUBLIC_INTERFACE
class LeaderboardStat(SQLModel, table=True):
    """
    ORM model for tracking user stats for leaderboard purposes.
    """
    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="user.id", unique=True)
    wins: int = Field(default=0, nullable=False, description="# of wins")
    losses: int = Field(default=0, nullable=False, description="# of losses")
    draws: int = Field(default=0, nullable=False, description="# of draws")
    total_games: int = Field(default=0, nullable=False, description="Games played")
    last_played: Optional[datetime] = Field(default=None, description="Datetime of last played game")

    user: Optional[User] = Relationship(back_populates="leaderboard_entry")
