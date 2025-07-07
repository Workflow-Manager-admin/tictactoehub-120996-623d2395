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
