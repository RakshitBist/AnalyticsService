#!/usr/bin/env bash
# Stops the dashboard, the three Java services and the Docker containers.
cd "$(dirname "$0")"
for port in 8090 8082 8083 8084; do
  pids=$(lsof -ti tcp:"$port" -sTCP:LISTEN 2>/dev/null || true)
  [ -n "$pids" ] && kill $pids && echo "Stopped whatever was on port $port"
done
docker compose stop
echo "Everything stopped. Your data is kept; ./start.sh brings it back."
