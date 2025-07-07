# Tic Tac Toe Backend API Reference

This document serves as the detailed reference for all public API endpoints exposed by the `tic_tac_toe_backend` FastAPI service. It is intended for frontend integration and developer use covering route specifications, request/response models, expected error codes, and practical usage notes.

_Last updated: 2024-06-11_

---

## Service Overview

- **Platform:** FastAPI (Python)
- **Base URL:** `/` (Typically runs on port 3001)
- **CORS:** Fully open (`*`) for all methods/headers, suitable for browser-based frontend.
- **Authentication:** None required (all routes public)

---

## Table of Contents

- [Health Check](#health-check)
- [Start New Game](#start-new-game)
- [Make a Move](#make-a-move)
- [Game Status](#game-status)
- [Leaderboard](#leaderboard)
- [Game History](#game-history)
- [Data Models](#data-models)
- [Error Handling](#error-handling)
- [Usage Notes](#usage-notes)
- [API Overview Diagram](#api-overview-diagram)

---

## Health Check

- **GET /**  
- **Purpose:** Confirm backend service is running.
- **Returns:**
  ```json
  { "message": "Healthy" }
  ```
- **Errors:** Never errors.

---

## Start New Game

- **POST /games/new**
- **Purpose:** Start a new public Tic Tac Toe game.
- **Request Body:**  
  ```json
  {
    "player_x_name": "Alice", // optional, default "Player X"
    "player_o_name": "Bob"    // optional, default "Player O"
  }
  ```
- **Response:**
  ```json
  { "game_id": 1 }
  ```
- **Errors:** None expected on valid input.

---

## Make a Move

- **POST /games/{game_id}/move**
- **Purpose:** Place a move in an existing game.
- **URL Params:**  
  - `game_id`: (integer) game identifier

- **Request Body:**
  ```json
  {
    "symbol": "X",        // "X" or "O"
    "position": 4         // integer from 0 to 8 (board cell index)
  }
  ```

- **Success Response:**
  ```json
  {
    "success": true,
    "next_turn": "O",
    "status": "active", // or "draw" or "win"
    "winner": null      // "X", "O", or null if still active/draw
  }
  ```

- **Error Responses:**
    | HTTP Code | Description            | Body Example                                                    |
    |-----------|-----------------------|-----------------------------------------------------------------|
    | 404       | Game not found        | `{ "detail": "Game not found" }`                                |
    | 400       | Game not active       | `{ "detail": "Game not active" }`                               |
    | 400       | Invalid symbol        | `{ "detail": "Invalid symbol" }`                                |
    | 400       | Not player's turn     | `{ "detail": "Not this player's turn" }`                        |
    | 400       | Cell already occupied | `{ "detail": "Cell already occupied" }`                         |

- **Edge Cases:**  
  - Moves out-of-turn, to an invalid cell, or after game conclusion will fail with code 400.

---

## Game Status

- **GET /games/{game_id}/status**
- **Purpose:** Retrieve current board state, move history, and game metadata.
- **URL Params:**  
  - `game_id`: (integer)

- **Response:** (`application/json`)
  ```json
  {
    "id": 1,
    "board_state": "XO XO O  ",
    "status": "active", // or "win", "draw"
    "current_turn": "X",
    "winner": null,
    "moves": [
      { "position": 0, "order": 0, "symbol": "X" },
      { "position": 1, "order": 1, "symbol": "O" }
      // ...
    ],
    "player_labels": {
      "X": "Alice",
      "O": "Bob"
    }
  }
  ```
- **Errors:**
    | HTTP Code | Description         | Body Example                      |
    |-----------|--------------------|-----------------------------------|
    | 404       | Game not found     | `{ "detail": "Game not found" }`  |

---

## Leaderboard

- **GET /leaderboard**
- **Purpose:** View win/loss/draw stats for X and O across all games (no user ties).
- **Response:**
  ```json
  [
    {
      "symbol": "X",
      "wins": 12,
      "losses": 9,
      "draws": 4,
      "total_games": 25,
      "last_played": "2024-06-10T20:05:07.567Z"
    },
    {
      "symbol": "O",
      "wins": 9,
      "losses": 12,
      "draws": 4,
      "total_games": 25,
      "last_played": "2024-06-10T20:05:07.567Z"
    }
  ]
  ```
- **Errors:** Never errors.

---

## Game History

- **GET /history**
- **Purpose:** Lists historical game data, including timestamps and results.
- **Response:**  
  ```json
  [
    {
      "game_id": 5,
      "created_at": "2024-06-10T15:02:00.003Z",
      "completed_at": "2024-06-10T15:20:53.608Z",
      "result": "draw"
    },
    {
      "game_id": 4,
      "created_at": "2024-06-09T12:32:11.321Z",
      "completed_at": null,
      "result": "in-progress"
    }
    // ...
  ]
  ```
- **Errors:** Never errors.

---

## Data Models

### GameCreateRequest

```json
{
  "player_x_name": "Player X",    // Optional; label for X (default)
  "player_o_name": "Player O"     // Optional; label for O (default)
}
```

### GameMoveRequest

```json
{
  "symbol": "X",     // "X" or "O"
  "position": 4      // Board index (0-8)
}
```

### GameStatusOut

- `id` (integer): Game ID
- `board_state` (string): 9-character string (cells "X", "O", or " ") in row-major order
- `status` (string): "active" | "win" | "draw"
- `current_turn` (string): "X" or "O"
- `winner` (string | null): "X", "O", or null
- `moves`: Array of `{ position, order, symbol }`
- `player_labels`: Object `{ "X": ..., "O": ... }`

### LeaderboardEntryOut

- `symbol` (string): "X" or "O"
- `wins` (int): Number of wins
- `losses` (int): Number of losses
- `draws` (int): Number of draws
- `total_games` (int): Games played
- `last_played` (string | null): ISO date

### GameHistoryEntry

- `game_id` (int)
- `created_at` (string): ISO date
- `completed_at` (string|null)
- `result` (string): "win" | "draw" | "in-progress"

#### Underlying ORM models (for reference)

- **Game**: Stores core game state and labels.
- **Move**: Tracks each move per game.
- **LeaderboardStat**: Deprecated (not used for API).

---

## Error Handling

- All validation errors use FastAPI-style responses:
  ```json
  { "detail": "Reason for failure" }
  ```
- Game not found = 404  
- Invalid operations (move after game over, out of turn, wrong symbol, cell full) = 400  
- No route requires or checks for player authentication.

---

## Usage Notes

- Games are fully public; no user authentication, session, or accounts.
- Multiple games can be played in parallel by different users via client-side tracking of `game_id`.
- Move sequence and board state are always kept consistent by server-side validation.
- The backend enforces Tic Tac Toe rules, disallowing illegal moves, out-of-order plays, or resuming finished games.
- Player labels are cosmetic and not bound to user identities.

---

## API Overview Diagram

```mermaid
graph TD
    A[POST /games/new] -- creates --> B((Game))
    A -- returns --> C[game_id]
    B -- referenced by --> D[POST /games/{game_id}/move]
    D -- updates --> B
    D -- errors on invalid input --> G[400/404]
    D -- triggers --> F[Victory/Draw Check]
    E[GET /games/{game_id}/status] -- shows state/moves of --> B
    H[GET /leaderboard] -- queries --> B
    I[GET /history] -- lists --> B
    C -- used in --> D
```

---

### For additional questions, consult backend code or `/docs` at the running backend instance.

