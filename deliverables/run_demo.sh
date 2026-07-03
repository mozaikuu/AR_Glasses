#!/usr/bin/env bash
set -euo pipefail

BASE_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$BASE_DIR"

if [ -f docker_image.tar ]; then
  echo "Loading Docker image..."
  docker load -i docker_image.tar
  echo "Running container on port 8000..."
  docker run --rm -p 8000:8000 --name smartglasses_demo smartglasses:deliverable
else
  echo "docker_image.tar not found — trying binary fallback..."
  if [ -x bin/app_demo ]; then
    ./bin/app_demo --demo-mode
  else
    echo "No runnable artifact found. See README.md"
    exit 2
  fi
fi
