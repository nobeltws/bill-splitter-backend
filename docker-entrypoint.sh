#!/bin/sh
set -e

echo "Running migrations..."
node node_modules/typeorm/cli.js migration:run -d dist/src/db/data-source.js

echo "Starting server..."
exec "$@"
