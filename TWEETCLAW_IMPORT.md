# TweetClaw Export Import

The Streamlit app can analyze reviewed X/Twitter exports from
[TweetClaw](https://github.com/Xquik-dev/tweetclaw) or Xquik without calling a
live social API from the dashboard.

1. Open the app.
2. Select `TweetClaw Export` in the platform selector.
3. Upload a TweetClaw CSV, JSON, JSONL, or NDJSON export.
4. Click `Fetch & Analyze`.

The importer maps common TweetClaw export fields into the app's existing
comment schema:

| App field | Accepted export fields |
| --- | --- |
| `text` | `text`, `full_text`, `tweet_text`, `tweet`, `content`, `body`, `message` |
| `published_at` | `created_at`, `createdAt`, `timestamp`, `date`, `time`, `published_at` |
| `author` | `author`, `username`, `screen_name`, `author_username`, `authorUsername`, `user` |
| `like_count` | `like_count`, `likes`, `favorite_count`, `favoriteCount` |

Rows without tweet text are skipped so the existing TextBlob, VADER, emotion,
hashtag, keyword, and chart flows keep working.
