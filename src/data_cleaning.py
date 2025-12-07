import pandas as pd
from textblob import TextBlob
from src.db_utils import get_connection

def clean_text(text):
    if not isinstance(text, str):
        return ""
    text = text.replace("\n", " ").strip()
    return text

def analyze_sentiment(text):
    blob = TextBlob(text)
    polarity = blob.sentiment.polarity
    subjectivity = blob.sentiment.subjectivity
    sentiment = (
        "positive" if polarity > 0.1
        else "negative" if polarity < -0.1
        else "neutral"
    )
    return sentiment, polarity, subjectivity

def update_sentiment_in_db():
    conn = get_connection()
    cur = conn.cursor()

    print("📌 Loading comments without sentiment from DB...")
    cur.execute("""
        SELECT comment_id, text 
        FROM youtube_comments
        WHERE sentiment IS NULL
    """)
    rows = cur.fetchall()

    if not rows:
        print("✅ All comments already have sentiment values.")
        cur.close()
        conn.close()
        return

    print(f"🔄 Updating sentiment values for {len(rows)} comments...")
    for comment_id, text in rows:
        text = clean_text(text)
        sentiment, polarity, subjectivity = analyze_sentiment(text)

        cur.execute("""
            UPDATE youtube_comments
            SET sentiment = %s, polarity = %s, subjectivity = %s
            WHERE comment_id = %s
        """, (sentiment, polarity, subjectivity, comment_id))

    conn.commit()
    cur.close()
    conn.close()

    print(f"🎉 Sentiment analysis completed & stored for {len(rows)} new comments!")

if __name__ == "__main__":
    update_sentiment_in_db()
