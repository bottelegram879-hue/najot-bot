#!/usr/bin/env bash
# Render start command: both bots in one free web service.
#  * @najotservis_bot — webhook + request form on $PORT (keeps the service awake)
#  * video bot        — polling in the background, restarted if it ever exits
cd "$(dirname "$0")"
( cd video_bot && while true; do python bot.py; sleep 5; done ) &
cd najot_servis && exec python -m bot
