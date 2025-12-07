# src/data_cleaning_vader.py

from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
import pandas as pd
from src.db_utils import get_connection
from transformer_models import TransformerSentimentModel, TransformerEmotionModel

sentiment_model = TransformerSentimentModel()
emotion_model = TransformerEmotionModel()

analyzer = SentimentIntensityAnalyzer()

def vader_score(text):
    if not isinstance(text, str) or text.strip() == "":
        return {"compound": 0.0, "pos": 0.0, "neu": 0.0, "neg": 0.0}
    return analyzer.polarity_scores(text)

def vader_label_from_compound(compound):
    # standard VADER thresholds
    if compound >= 0.05:
        return "positive"
    if compound <= -0.05:
        return "negative"
    return "neutral"

def add_vader_to_df(df, text_col="text"):
    """
    Input: df (pandas.DataFrame) with a text_col
    Returns: df with new columns:
      - vader_compound, vader_positive, vader_neutral, vader_negative, vader_label
    """
    df = df.copy()
    # ensure text exists
    df[text_col] = df[text_col].fillna("").astype(str)

    compounds = []
    pos_scores = []
    neu_scores = []
    neg_scores = []
    labels = []

    for txt in df[text_col]:
        s = vader_score(txt)
        compounds.append(s["compound"])
        pos_scores.append(s["pos"])
        neu_scores.append(s["neu"])
        neg_scores.append(s["neg"])
        labels.append(vader_label_from_compound(s["compound"]))

    df["vader_compound"] = compounds
    df["vader_positive"] = pos_scores
    df["vader_neutral"] = neu_scores
    df["vader_negative"] = neg_scores
    df["vader_label"] = labels

    return df

def update_vader_in_db(only_null=True, batch_size=500):
    """
    Compute VADER on rows in DB and write results back.
    If only_null=True, it will update only rows where vader_label IS NULL.
    Processes in batches to avoid huge queries.
    """
    conn = get_connection()
    cur = conn.cursor()

    if only_null:
        cur.execute("SELECT comment_id, text FROM youtube_comments WHERE vader_label IS NULL")
    else:
        cur.execute("SELECT comment_id, text FROM youtube_comments")

    rows = cur.fetchall()
    if not rows:
        print("No rows to update for VADER.")
        cur.close(); conn.close(); return

    print(f"Found {len(rows)} rows to analyze with VADER.")

    # process in batches
    i = 0
    while i < len(rows):
        batch = rows[i:i+batch_size]
        updates = []
        for comment_id, text in batch:
            s = vader_score(text or "")
            label = vader_label_from_compound(s["compound"])
            updates.append((s["compound"], s["pos"], s["neu"], s["neg"], label, comment_id))

        args_str = ",".join(["(%s,%s,%s,%s,%s,%s)"] * len(updates))
        # We'll just run individual updates to keep it simple and safe
        for comp, p, neu, neg, lab, cid in updates:
            cur.execute("""
                UPDATE youtube_comments
                SET vader_compound=%s, vader_positive=%s, vader_neutral=%s, vader_negative=%s, vader_label=%s
                WHERE comment_id = %s
            """, (comp, p, neu, neg, lab, cid))
        conn.commit()
        i += batch_size
        print(f"Processed {i if i < len(rows) else len(rows)} / {len(rows)}")

    cur.close()
    conn.close()
    print("VADER update complete.")

# ---------------------------------------------------------
# TRANSFORMER SENTIMENT + EMOTION for batches in the DB
# ---------------------------------------------------------
def update_transformers_in_db(only_null=True, batch_size=200):
    """
    Applies RoBERTa sentiment + DistilRoBERTa emotion to DB rows.
    Writes results to DB columns:
       transformer_sentiment, t_positive, t_negative, t_neutral,
       joy, anger, fear, sadness, disgust, surprise, trust, anticipation
    """
    conn = get_connection()
    cur = conn.cursor()

    if only_null:
        cur.execute("""
            SELECT comment_id, text 
            FROM youtube_comments 
            WHERE transformer_sentiment IS NULL
        """)
    else:
        cur.execute("SELECT comment_id, text FROM youtube_comments")

    rows = cur.fetchall()
    if not rows:
        print("No rows to update for Transformer models.")
        cur.close(); conn.close(); return

    print(f"Found {len(rows)} rows for transformer analysis.")

    i = 0
    while i < len(rows):
        batch = rows[i:i+batch_size]
        texts = [(t or "") for _, t in batch]

        # ---- Transformer sentiment ----
        sent_results = sentiment_model.predict(texts)
        # ---- Transformer emotions ----
        emo_results = emotion_model.predict(texts)

        # write results
        for (comment_id, text), s_res, e_res in zip(batch, sent_results, emo_results):
            cur.execute("""
                UPDATE youtube_comments
                SET transformer_sentimen_

