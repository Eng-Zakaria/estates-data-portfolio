#!/bin/sh
# P15 Node-RED entrypoint.
#
# Node-RED 4 always loads <userDir>/flows.json and ignores settings.flowFile
# (verified on 4.0.9), and single-file bind mounts are unreliable on Docker
# Desktop/Windows. So the project is mounted read-only at /data/p15 and this
# script copies the committed flow and settings into the writable user dir
# before starting Node-RED.
set -e

SRC=/data/p15
DEST=/data

if [ ! -f "$DEST/flows.json" ] || [ "${P15_FORCE_FLOWS:-0}" = "1" ]; then
  cp "$SRC/flows/p15_bms.json" "$DEST/flows.json"
  echo "entrypoint: installed flows/p15_bms.json -> $DEST/flows.json"
fi

cp "$SRC/flows/settings.js" "$DEST/settings.js"
echo "entrypoint: installed flows/settings.js -> $DEST/settings.js"

# node-red-contrib-postgresql is installed into /data/node_modules by the image
# build; keep the user dir writable so nothing else clobbers it
mkdir -p "$DEST/node_modules"

exec node-red --userDir "$DEST" "$@"
