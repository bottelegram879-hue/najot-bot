# NAJOT SERVIS bots (Render)

* `najot_servis/` — @najotservis_bot (truck repair requests, website form as Telegram Mini App)
* `video_bot/` — video downloader bot

Render web service: build `pip install -r najot_servis/requirements.txt -r video_bot/requirements.txt`,
start `bash start.sh`. Secrets are set as environment variables in Render, never in this repository:
`BOT_TOKEN`, `VIDEO_BOT_TOKEN`, `DATABASE_URL`, `OWNER_USERNAMES`, `MASTER_USERNAMES`, `NOTIFY_TARGETS`, `PHONES`.
