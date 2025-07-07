# tictactoehub-120996-623d2395

## Backend FastAPI Server Startup Instructions

If you encounter an import error when running:
```shell
uvicorn src.api.main:app --host 0.0.0.0 --port 3001
```
it is due to Python's module resolution and the working directory.

### Recommended Command (from backend root)

**Change directory to the backend root:**
```shell
cd tic_tac_toe_backend
```

**Then run (PYTHONPATH=. helps ensure correct imports):**
```shell
PYTHONPATH=. uvicorn src.api.main:app --host 0.0.0.0 --port 3001
```

Alternatively, run from `src` subdir:
```shell
cd tic_tac_toe_backend/src
uvicorn api.main:app --host 0.0.0.0 --port 3001
```

### Notes:
- The `src.api.main:app` syntax requires that you run the Uvicorn command from a directory where `src` is importable (i.e., on the PYTHONPATH).
- If you see errors like "No module named 'src'" or import failures in `uvicorn/importer.py`, check your current working directory and ensure PYTHONPATH includes `.` or the full path to your source root.
- In production or Docker, update your Dockerfile or entrypoint to set `WORKDIR` and `PYTHONPATH` correctly.

---

## Backend Diagnostics: Endpoint & CORS Testing

To troubleshoot persistent frontend fetch errors (e.g., "Failed to fetch" or CORS issues):

1. Make sure backend is running at the expected URL/port (default: https://...:3001).
2. Run the diagnostic script to check endpoint accessibility and CORS headers:

    ```sh
    cd tic_tac_toe_backend
    chmod +x test_backend_cors_and_accessibility.sh
    ./test_backend_cors_and_accessibility.sh [BACKEND_BASE_URL] [FRONTEND_ORIGIN]
    # Example:
    # ./test_backend_cors_and_accessibility.sh https://vscode-internal-347728-beta.beta01.cloud.kavia.ai:3001 http://localhost:4000
    ```

3. Review the script output to ensure:
    - HTTP status 200 for GET and OPTIONS to `/cors-test` and `/leaderboard`
    - Presence of `Access-Control-Allow-Origin: *` in response headers
    - No protocol mismatch (http/https)
    - Port/network connectivity is allowed

If CORS headers or connectivity is incorrect, review CORS settings in `src/api/main.py`.

For further debugging steps and code-level recommendations, see extensive commentary in `src/api/main.py` (search "CORS", "diagnose", or "fetch error").
