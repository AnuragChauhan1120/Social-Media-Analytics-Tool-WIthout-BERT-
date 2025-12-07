import requests
import pandas as pd
from datetime import datetime

def fetch_twitter_comments(tweet_url: str):
    # Extract tweet ID
    tweet_id = tweet_url.split("/")[-1]

    api_url = f"https://api.tweetpik.com/v2/tweet/{tweet_id}/replies?count=100"

    headers = {
        "User-Agent": "Mozilla/5.0 (SocialAnalyticsTool)"
    }

    try:
        res = requests.get(api_url, headers=headers, timeout=10)
        data = res.json()
    except:
        return pd.DataFrame()

    if "data" not in data:
        return pd.DataFrame()

    rows = []
    for r in data["data"]:
        try:
            rows.append({
                "comment_id": r.get("id"),
                "author": r.get("author", {}).get("username", ""),
                "text": r.get("full_text", ""),
                "published_at": datetime.fromisoformat(r.get("created_at", "").replace("Z", "+00:00")),
                "like_count": r.get("favorite_count", 0),
                "platform": "twitter",
                "post_id": tweet_id
            })
        except:
            continue

    return pd.DataFrame(rows)
