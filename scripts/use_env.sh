#!/usr/bin/env bash
# Activates a config profile for both Docker Compose and the app itself.
#
# Usage:
#   ./scripts/use_env.sh local
#   ./scripts/use_env.sh staging
#   ./scripts/use_env.sh production
#
# What it does: copies .env.<profile> -> .env (the file Docker Compose
# reads automatically for both its own ${VAR} interpolation, e.g. the
# mysql service's password, AND for injecting env vars into the api /
# celery_worker containers). The profile file also contains APP_ENV=<profile>,
# so once it's copied in, the app picks the matching settings automatically.
#
# For running WITHOUT Docker (bare uvicorn on your host), you don't need
# this script — just export APP_ENV yourself:
#   APP_ENV=staging uvicorn app.main:app --reload
# and the app will read .env.staging directly.

set -euo pipefail

PROFILE="${1:-}"
VALID_PROFILES=("local" "staging" "production")

if [[ -z "$PROFILE" ]]; then
  echo "Usage: $0 <local|staging|production>"
  exit 1
fi

if [[ ! " ${VALID_PROFILES[*]} " =~ " ${PROFILE} " ]]; then
  echo "Error: '$PROFILE' is not a valid profile. Must be one of: ${VALID_PROFILES[*]}"
  exit 1
fi

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(dirname "$SCRIPT_DIR")"
SOURCE_FILE="$ROOT_DIR/.env.$PROFILE"
DEST_FILE="$ROOT_DIR/.env"

if [[ ! -f "$SOURCE_FILE" ]]; then
  echo "Error: $SOURCE_FILE does not exist."
  echo "Copy .env.$PROFILE.example to .env.$PROFILE and fill in real values first."
  exit 1
fi

cp "$SOURCE_FILE" "$DEST_FILE"
echo "Activated profile: $PROFILE"
echo "  $SOURCE_FILE -> $DEST_FILE"
echo ""
echo "Now run: docker compose up --build"
