#!/bin/bash
# Diagnostic script to verify backend endpoint reachability and CORS headers.
# Usage: ./test_backend_cors_and_accessibility.sh [BACKEND_BASE_URL] [FRONTEND_ORIGIN]
# Default BACKEND_BASE_URL: https://vscode-internal-347728-beta.beta01.cloud.kavia.ai:3001
# Default FRONTEND_ORIGIN: http://localhost:4000

BACKEND_BASE_URL="${1:-https://vscode-internal-347728-beta.beta01.cloud.kavia.ai:3001}"
FRONTEND_ORIGIN="${2:-http://localhost:4000}"

echo "=== [1] Testing basic GET /cors-test ==="
curl -i -X GET "$BACKEND_BASE_URL/cors-test"

echo -e "\n=== [2] Testing GET /cors-test with Origin header from frontend ($FRONTEND_ORIGIN) ==="
curl -i -X GET "$BACKEND_BASE_URL/cors-test" -H "Origin: $FRONTEND_ORIGIN"

echo -e "\n=== [3] Testing preflight OPTIONS /cors-test ==="
curl -i -X OPTIONS "$BACKEND_BASE_URL/cors-test" \
  -H "Origin: $FRONTEND_ORIGIN" \
  -H "Access-Control-Request-Method: GET" \
  -H "Access-Control-Request-Headers: Content-Type"

echo -e "\n=== [4] Testing GET /leaderboard with Origin header from frontend ($FRONTEND_ORIGIN) ==="
curl -i -X GET "$BACKEND_BASE_URL/leaderboard" -H "Origin: $FRONTEND_ORIGIN"

echo -e "\n==== CORS and connectivity checks complete ===="
echo "Manual checks:"
echo "- Make sure Access-Control-Allow-Origin: * is present in responses."
echo "- Confirm status 200 on GET and OPTIONS."
echo "- If using HTTPS on the frontend, backend must also use HTTPS."
echo "- Run this from inside the environment where your frontend runs (e.g., cloud, local dev)."
