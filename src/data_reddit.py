import requests
import pandas as pd
from datetime import datetime

def extract_post_id_from_url(url: str):
    """
    Converts a Reddit post URL into the .json API URL.
    """
    if not url.endswith(".json"):
        if url.endswith("/"):
            url = url[:-1]
        url = url + ".json"
    return url

def fetch_reddit_comments(post_url: str):
    """
    Fetches Reddit comments via the public JSON endpoint.
    Returns a normalized pandas DataFrame.
    No API keys required.
    """

    json_url = extract_post_id_from_url(post_url)

    headers = {
        "User-Agent": "Mozilla/5.0 (SocialAnalyticsTool)"
    }

    try:
        res = requests.get(json_url, headers=headers, timeout=10)
        data = res.json()
    except Exception as e:
        print("Reddit fetch error:", e)
        return pd.DataFrame()

    # Comments are in data[1]['data']['children']
    try:
        comments_raw = data[1]['data']['children']
    except:
        return pd.DataFrame()

    rows = []
    for c in comments_raw:
        if c["kind"] != "t1":  # t1 = comment
            continue

        body = c["data"].get("body", "")
        comment_id = c["data"].get("id", "")
        author = c["data"].get("author", "")
        ups = c["data"].get("ups", 0)
        created_utc = c["data"].get("created_utc", None)

        if created_utc:
            published = datetime.utcfromtimestamp(created_utc)
        else:
            published = None

        rows.append({
            "comment_id": comment_id,
            "author": author,
            "text": body,
            "published_at": published,
            "like_count": ups,
            "platform": "reddit",
            "post_id": c["data"].get("link_id", "")
        })

    df = pd.DataFrame(rows)
    return df
