#!/usr/bin/env bash
# Starts the whole analytics system and opens the dashboard.
# Usage: ./start.sh        Stop everything with: ./stop.sh
set -euo pipefail
cd "$(dirname "$0")"
ROOT="$(pwd)"
mkdir -p services logs

say()  { printf '\n\033[1m%s\033[0m\n' "$*"; }
up()   { nc -z localhost "$1" >/dev/null 2>&1; }

# 1. Docker Desktop
say "1/5  Checking Docker"
if ! docker info >/dev/null 2>&1; then
  echo "Docker isn't running, opening Docker Desktop..."
  open -a Docker 2>/dev/null || true
  for _ in $(seq 1 60); do docker info >/dev/null 2>&1 && break; sleep 2; done
fi
docker info >/dev/null 2>&1 || { echo "Docker still isn't running. Open Docker Desktop, wait for it, then run ./start.sh again."; exit 1; }

# 2. Kafka, PostgreSQL, Redis
say "2/5  Starting Kafka, PostgreSQL and Redis"
docker compose up -d
until docker compose exec -T postgres pg_isready -U postgres >/dev/null 2>&1; do sleep 1; done
until docker compose exec -T redis redis-cli ping >/dev/null 2>&1; do sleep 1; done
# Register the demo app (this is the Registration service's job; that repo isn't available)
docker compose exec -T redis redis-cli SET app_token_versionapp1 1 >/dev/null
docker compose exec -T redis redis-cli SET app_statusapp1 active >/dev/null
echo "Ready. Demo app 'app1' registered in Redis."

# 3. Service code
say "3/5  Getting the latest service code"
for s in Producer Consumer Reporter; do
  d="services/Analytics$s"
  if [ -d "$d/.git" ]; then
    git -C "$d" pull -q --ff-only || echo "  (couldn't update $d, using the copy you have)"
  else
    git clone -q "https://github.com/RakshitBist/Analytics$s" "$d"
  fi
  chmod +x "$d/mvnw"
  echo "  Analytics$s ok"
done

# 4. Java services (logs go to logs/<name>.log)
say "4/5  Starting the Java services (the first run downloads libraries, 2-5 minutes)"
run() {
  local name="$1" port="$2" args="$3"
  if up "$port"; then echo "  $name already running on $port"; return; fi
  ( cd "services/Analytics$name" && nohup ./mvnw -q spring-boot:run -Dspring-boot.run.arguments="$args" > "$ROOT/logs/$name.log" 2>&1 & )
  echo "  $name starting (log: logs/$name.log)"
}
run Consumer 8083 "--server.port=8083 --spring.kafka.bootstrap-servers=localhost:9094"
run Producer 8082 "--spring.kafka.bootstrap-servers=localhost:9094"
run Reporter 8084 ""

for pair in Consumer:8083 Producer:8082 Reporter:8084; do
  name="${pair%%:*}"; port="${pair##*:}"; waited=0
  until up "$port"; do
    sleep 3; waited=$((waited+3))
    if [ "$waited" -ge 600 ]; then echo "  $name didn't start. Look at logs/$name.log"; exit 1; fi
  done
  echo "  $name is up on $port"
done

# 5. Dashboard
say "5/5  Starting the dashboard"
if ! up 8090; then
  nohup python3 dashboard.py > logs/dashboard.log 2>&1 &
  sleep 1
fi
open http://localhost:8090/demo 2>/dev/null || true
say "All running: http://localhost:8090/demo   (stop with ./stop.sh)"
