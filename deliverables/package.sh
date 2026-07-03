#!/usr/bin/env bash
set -euo pipefail

BASE_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$BASE_DIR"

echo "Building Docker image 'smartglasses:deliverable' (if Dockerfile present)"
if [ -f ../Dockerfile ]; then
  docker build -t smartglasses:deliverable ..
else
  echo "No Dockerfile found in repo root. Skipping docker build."
fi

if docker image inspect smartglasses:deliverable > /dev/null 2>&1; then
  echo "Saving docker image to docker_image.tar..."
  docker save smartglasses:deliverable -o docker_image.tar
fi

echo "Generating checksums..."
sh -c 'sha256sum * > checksums.sha256'

if command -v gpg >/dev/null 2>&1; then
  echo "Signing checksums.sha256"
  gpg --output checksums.sha256.sig --detach-sign checksums.sha256
else
  echo "gpg not found; skipping signature generation"
fi

echo "Packaging deliverables.zip"
zip -r ../deliverables.zip ./*

echo "Done"
