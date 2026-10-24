#!/usr/bin/env bash
# Render start command: @najotservis_bot - webhook + request form on $PORT
cd "$(dirname "$0")"
cd najot_servis && exec python -m bot
