import os
import re
import requests
import pandas as pd
import streamlit as st
from dotenv import load_dotenv
from pathlib import Path

# ----------------------------------------------------
# LOAD API KEY (Streamlit Cloud → st.secrets)
# Local development → .env file
# ----------------------------------------------------
env_path = Path(__file__).resolve().parent.parent / ".env"
load_dotenv(env_path)

YOUTUBE_API_KEY = st.secrets.get("YOUTUBE_API_KEY") or os.getenv("YOUTUBE_API_KEY")

if not YOUTUBE_API_KEY:
    raise ValueError(
        "❌ YouTube API key not found.\n"
        "Set YOUTUBE_API_KEY in Streamlit Cloud → Secrets."
    )


# ----------------------------------------------------
# Extract Video ID
# ----------------------------------------------------
def extract_video_id(url):
    match = re.search(r"v=([a-zA-Z0-9_-]+)", url)
    return match.group(1) if match else None


# ----------------------------------------------------
# Fetch Comments
# ----------------------------------------------------
def get_comments(video_url, max_results=200):
    video_id = extract_video_id(video_url)
    if not video_id:
        raise ValueError("Invalid YouTube video URL")

    comments = []
    next_page_token = None

    while len(comments) < max_results:
        api_url = "https://www.googleapis.com/youtube/v3/commentThreads"
        params = {
            "part": "snippet",
            "videoId": video_id,
            "key": YOUTUBE_API_KEY,
            "maxResults": 100,
            "pageToken": next_page_token,
            "textFormat": "plainText"
        }

        response = requests.get(api_url, params=params)
        data = response.json()

        if "error" in data:
            # More helpful error
            message = data["error"]["message"]
            raise Exception(f"❌ YouTube API Error: {message}")

        for item in data.get("items", []):
            snippet = item["snippet"]["topLevelComment"]["snippet"]
            comments.append({
                "comment_id": item["id"],
                "author": snippet.get("authorDisplayName"),
                "comment": snippet.get("textDisplay"),
                "likes": snippet.get("likeCount"),
                "published_at": snippet.get("publishedAt"),
                "video_id": video_id,
                "platform": "youtube"
            })

        next_page_token = data.get("nextPageToken")
        if not next_page_token:
            break

    return pd.DataFrame(comments[:max_results])


# ----------------------------------------------------
# Optional: DB utilities
# ----------------------------------------------------
from src.db_utils import create_comments_table, insert_comments

if __name__ == "__main__":
    print("\nFetching comments...")
    df = get_comments("https://www.youtube.com/watch?v=McXJj7sjcZ0", max_results=200)

    df = df.rename(columns={
        "comment": "text",
        "likes": "like_count"
    })

    create_comments_table()
    insert_comments(df)

    print("✅ Comments inserted into PostgreSQL!\n")
