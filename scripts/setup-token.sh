#!/bin/sh
set -eu
cd "$(dirname "$0")/.."
# Explicit operator command. The token is never in application logs or tracked files.
sed -n 's/^SETUP_TOKEN=//p' .env
