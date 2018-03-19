#!/bin/sh

set -e

echo "CONFIG API"

cd /app
python config.py

echo "START GUILLOTINA SERVER"

exec "$@"