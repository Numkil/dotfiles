#!/usr/bin/env bash
set -euo pipefail

# Fetch a file from a live Statik server for the current project.
# Usage: fetch.sh <filename> [project-directory]
#
# The project name is derived from the current working directory name,
# or can be overridden via the second argument.

if [ -z "${1:-}" ]; then
    echo "Usage: fetch.sh <filename> [project-name]" >&2
    exit 1
fi

FILE="$1"
PROJECT="${2:-$(basename "$PWD")}"

HOST="${PROJECT}livestatikbe@${PROJECT}.ssh.statik.be"
REMOTE_PATH="/data/sites/web/${PROJECT}livestatikbe/subsites/${PROJECT}.live.statik.be/current/${FILE}"

echo "Downloading ${FILE} from ${PROJECT} live server..."
echo "  Host: ${HOST}"
echo "  Remote: ${REMOTE_PATH}"
echo "  Local:  ${FILE}"

scp -r "${HOST}:${REMOTE_PATH}" "${FILE}"

echo "Done."
