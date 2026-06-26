#!/bin/sh
set -e

if [ -n "$EXTRA_PIP_PACKAGES" ]; then
    # Strip surrounding quotes if present
    CLEAN_PACKAGES=$(echo "$EXTRA_PIP_PACKAGES" | sed 's/^"\(.*\)"$/\1/')
    CLEAN_PACKAGES=$(echo "$CLEAN_PACKAGES" | tr ',' ' ')
    echo "Installing extra pip packages: $CLEAN_PACKAGES"
    pip install --no-cache-dir $CLEAN_PACKAGES
fi

exec "$@"