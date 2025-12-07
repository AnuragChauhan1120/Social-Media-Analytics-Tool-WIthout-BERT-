# scraper_api.py
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
import re, traceback

app = FastAPI(title="Scraper API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

try:
    import snscrape.modules.twitter as sntwitter
except:
    sntwitter = None

try:
    import instaloader
except:
    instaloader = None

from textblob import TextBlob
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
_vader = SentimentIntensityAnalyzer()

def extract_tweet_id(url):
    m = re.search(r"status/(\d+)", url)
    return m.group(1) if m else None

@app.get("/scrape/twitter")
def scrape_twitter(url: str = Query(...)):
    if not sntwitter:
        raise HTTPException(500, "snscrape missing")
    tid = extract_tweet_id(url)
    if not tid:
        raise HTTPException(400, "Invalid tweet URL")

    results = []
    for i, t in enumerate(sntwitter.TwitterSearchScraper(f"conversation_id:{tid}").get_items()):
        txt = t.rawContent if hasattr(t, "rawContent") else t.content
        results.append({
            "author": t.user.username,
            "text": txt,
            "likes": getattr(t, "likeCount", 0),
            "time": str(getattr(t, "date", "")),
            "sentiment": _vader.polarity_scores(txt)
        })
        if i > 300:
            break
    return {"comments": results, "count": len(results)}

def extract_shortcode(url):
    m = re.search(r"/p/([^/?#]+)", url)
    return m.group(1) if m else None

@app.get("/scrape/instagram")
def scrape_instagram(url: str = Query(...)):
    if not instaloader:
        raise HTTPException(500, "instaloader missing")

    shortcode = extract_shortcode(url)
    if not shortcode:
        raise HTTPException(400, "Invalid Instagram URL")

    L = instaloader.Instaloader()
    post = instaloader.Post.from_shortcode(L.context, shortcode)

    out = []
    for c in post.get_comments():
        txt = c.text
        out.append({
            "author": c.owner.username,
            "text": txt,
            "likes": getattr(c, "likes_count", 0),
            "time": str(getattr(c, "created_at_utc", "")),
            "sentiment": _vader.polarity_scores(txt)
        })

    return {"comments": out, "count": len(out)}
