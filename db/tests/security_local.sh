#!/usr/bin/env bash
# Disposable PostgreSQL 17 with TLS; never reads project .env credentials.
set -euo pipefail
root_dir="$(cd "$(dirname "$0")/../.." && pwd)"
test_python="${BM_TEST_PYTHON:-python3}"
test_dir="$(mktemp -d)"
container="bm-security-${RANDOM}-$$"
cleanup() {
  docker rm -f -v "$container" >/dev/null 2>&1 || true
  rm -rf "$test_dir"
}
trap cleanup EXIT
openssl req -x509 -newkey rsa:2048 -nodes -days 1 \
  -keyout "$test_dir/server.key" -out "$test_dir/server.crt" \
  -subj /CN=localhost -addext subjectAltName=DNS:localhost 2>/dev/null
docker run -d --name "$container" -e POSTGRES_PASSWORD=local-security-test \
  -p 127.0.0.1::5432 -v "$test_dir:/tls:ro" --entrypoint sh postgres:17-alpine -c '
    cp /tls/server.key /tmp/server.key
    chown postgres:postgres /tmp/server.key
    chmod 600 /tmp/server.key
    exec docker-entrypoint.sh postgres -c ssl=on \
      -c ssl_cert_file=/tls/server.crt -c ssl_key_file=/tmp/server.key
  ' >/dev/null
ready=0
for i in {1..30}; do
  if docker exec "$container" pg_isready -U postgres >/dev/null 2>&1; then
    ready=1
    break
  fi
  sleep 1
done
if [[ "$ready" != 1 ]]; then
  docker logs "$container"
  exit 1
fi
test_port="$(docker port "$container" 5432/tcp | awk -F: '{print $NF}')"
export BM_SECURITY_TEST_DSN="host=localhost port=$test_port dbname=postgres user=postgres password=local-security-test"
export BM_SECURITY_TEST_CA="$test_dir/server.crt"
cd "$root_dir"
"$test_python" -m pytest db/tests/test_security_boundaries.py db/tests/test_materialisieren.py "$@"
