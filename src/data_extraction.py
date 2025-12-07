import os
import re
import requests
import pandas as pd
from dotenv import load_dotenv
from pathlib import Path

# ✅ Load API credentials
env_path = Path(__file__).resolve().parent.parent / ".env"
load_dotenv(env_path)

print("Loaded ENV from:", env_path)
YOUTUBE_API_KEY = os.getenv("YOUTUBE_API_KEY")
print("API KEY LOADED:", YOUTUBE_API_KEY)


def extract_video_id(url):
    """Extract YouTube video ID from URL."""
    match = re.search(r"v=([a-zA-Z0-9_-]+)", url)
    return match.group(1) if match else None


def get_comments(video_url, max_results=200):
    """Fetch YouTube comments into a DataFrame."""
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
            raise Exception(data["error"]["message"])

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


from db_utils import create_comments_table, insert_comments

if __name__ == "__main__":
    print("\nFetching comments...")
    df = get_comments("https://www.youtube.com/watch?v=McXJj7sjcZ0", max_results=200)

# Remove this OR wrap it in a test block
# df = get_comments("some_video", 100)
# if df is not None and not df.empty:
#     print(df.head())


    df = df.rename(columns={
    "comment": "text",
    "likes": "like_count"  # ✅ Ensure correct matching
})
  # ✅ FIX ADDED HERE

    create_comments_table()
    insert_comments(df)
    print("✅ Comments inserted into PostgreSQL!\n")

