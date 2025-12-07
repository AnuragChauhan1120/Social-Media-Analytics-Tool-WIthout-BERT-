import requests
import pandas as pd
from datetime import datetime

def extract_shortcode(url):
    for part in url.split("/"):
        if len(part) == 11:
            return part
    return None

def fetch_instagram_comments(post_url: str):
    shortcode = extract_shortcode(post_url)
    if not shortcode:
        return pd.DataFrame()

    api_url = f"https://www.ddinstagram.com/p/{shortcode}/?__a=1&__d=1"

    headers = {
        "User-Agent": "Mozilla/5.0 (SocialAnalyticsTool)"
    }

    try:
        res = requests.get(api_url, headers=headers, timeout=10)
        data = res.json()
    except:
        return pd.DataFrame()

    try:
        edges = data["graphql"]["shortcode_media"]["edge_media_to_parent_comment"]["edges"]
    except:
        return pd.DataFrame()

    rows = []
    for node in edges:
        c = node["node"]
        rows.append({
            "comment_id": c["id"],
            "author": c["owner"]["username"],
            "text": c["text"],
            "published_at": datetime.utcfromtimestamp(c["created_at"]),
            "like_count": c.get("edge_liked_by", {}).get("count", 0),
            "platform": "instagram",
            "post_id": shortcode
        })

    return pd.DataFrame(rows)
