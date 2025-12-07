# top-of-file path hack to ensure imports resolve when streamlit starts the script
from keyword_analysis import get_hashtag_counts, get_keyword_counts
import plotly.express as px
import io
import sys, os
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime
from textblob import TextBlob
import matplotlib.pyplot as plt
import streamlit.components.v1 as components

# local helpers
from src.data_extraction import get_comments
from src.utils_visuals import (
    plot_sentiment_bar, plot_sentiment_pie, plot_likes_vs_sentiment,
    make_wordcloud_figure, format_comment_card, timeseries_sentiment
)
from src.db_utils import create_comments_table, insert_comments

# Page config
st.set_page_config(page_title="Cyber Analytics — YouTube Sentiment", layout="wide")
st.markdown("<style>body{background:#0b0f14;color:#cfefff}</style>", unsafe_allow_html=True)

# --- hologram header (Glass Hologram effect) ---
st.markdown("""
<style>
.holo {
  margin: 12px 0 18px 0;
  padding: 16px;
  border-radius:12px;
  background: linear-gradient(135deg, rgba(1,18,30,0.55), rgba(2,35,50,0.4));
  box-shadow: 0 8px 30px rgba(0,225,255,0.06);
  border: 1px solid rgba(0,225,255,0.12);
  backdrop-filter: blur(6px) saturate(120%);
}
.holo h1 {
  margin: 0; color: #00E1FF; font-weight:700; letter-spacing:0.6px;
  text-shadow: 0 2px 8px rgba(0,225,255,0.08);
}
.holo p {margin:2px 0 0 0; color:#9fdfff}
</style>
<div class="holo">
  <h1>🔮 Cyber Analytics — YouTube Sentiment</h1>
  <p>•Paste a content URL and analyze</p>
</div>
""", unsafe_allow_html=True)

# layout: left sidebar for controls, main area for visuals
platform = st.sidebar.selectbox(
    "Platform",
    ["YouTube", "Reddit", "Twitter", "Instagram"],
    index=0
)
if platform == "YouTube":
    input_label = "Paste YouTube Video URL"
elif platform == "Reddit":
    input_label = "Paste Reddit Post URL"
elif platform == "Twitter":
    input_label = "Paste Tweet URL"
else:
    input_label = "Paste Instagram Post URL"

with st.sidebar:
    st.header("Controls")
    input_url = st.text_input(input_label, value="")
    max_comments = st.slider("Max comments to fetch", min_value=50, max_value=1000, value=300, step=50)
    fetch_btn = st.button("Fetch & Analyze")
    st.markdown("---")
    st.markdown("Display")
    n_display = st.slider("How many comment cards to show", min_value=5, max_value=50, value=10, step=5)
    sort_opt = st.selectbox("Sort comments by", options=["Most liked","Most recent","Most positive","Most negative"])
    st.markdown("---")
    save_to_db = st.button("Save results to DB")
    st.markdown("Save only when you want to keep this analysis in DB.", unsafe_allow_html=True)
    model_choice = st.sidebar.selectbox("Sentiment model", options=["TextBlob (default)", "VADER"], index=0)
    use_emotions = st.sidebar.checkbox("Enable Emotion Analysis", value=True)

# placeholders
status = st.empty()
top_stats = st.columns([1,1,1])
viz_col1, viz_col2 = st.columns([2,1])

# helper: local sentiment using TextBlob
def analyze_textblob(text):
    blob = TextBlob(text or "")
    polarity = round(blob.sentiment.polarity, 4)
    subjectivity = round(blob.sentiment.subjectivity, 4)
    if polarity > 0.1:
        sentiment = "positive"
    elif polarity < -0.1:
        sentiment = "negative"
    else:
        sentiment = "neutral"
    return polarity, subjectivity, sentiment

# state holder
if "last_df" not in st.session_state:
    st.session_state.last_df = pd.DataFrame()

def prepare_df_for_display(raw_df):
    df = raw_df.copy()
    # standardize columns if needed
    if 'comment' in df.columns and 'text' not in df.columns:
        df = df.rename(columns={'comment':'text'})
    if 'likes' in df.columns and 'like_count' not in df.columns:
        df = df.rename(columns={'likes':'like_count'})
    # ensure expected columns exist
    for c in ['comment_id','video_id','author','text','published_at','like_count']:
        if c not in df.columns:
            df[c] = None
    # analyze sentiment locally (TextBlob baseline)
    pols, subs, sents = zip(*df['text'].fillna("").astype(str).map(analyze_textblob))
    df['sentiment_score'] = pols
    df['subjectivity'] = subs
    df['sentiment'] = sents
    # normalize published date display
    try:
        df['published_at'] = pd.to_datetime(df['published_at'], errors='coerce')
    except:
        pass
    return df

# import VADER helper safely
try:
    from src.data_cleaning_vader import add_vader_to_df
except Exception:
    add_vader_to_df = None

# ---------------------------
# Fetch & analyze flow
# ---------------------------
if fetch_btn:

    # -----------------------
    # REDDIT BRANCH
    # -----------------------
    if platform == "Reddit":
        try:
            from src.data_reddit import fetch_reddit_comments
        except Exception as e:
            status.error(f"Reddit module import failed: {e}")
            st.stop()

        status.info("Fetching Reddit comments...")
        try:
            raw = fetch_reddit_comments(input_url)
            if raw is None or raw.empty:
                status.warning("No Reddit comments found.")
                st.stop()
            df = prepare_df_for_display(raw)
            st.session_state.last_df = df
            status.success(f"Fetched {len(df)} Reddit comments.")
        except Exception as e:
            status.error(f"Error fetching Reddit comments: {e}")
            st.stop()

    # -----------------------
    # YOUTUBE BRANCH
    # -----------------------
    elif platform == "YouTube":
        if not input_url:
            status.error("Please paste a valid YouTube video URL")
            st.stop()
        try:
            status.info("Fetching comments from YouTube...")
            raw = get_comments(input_url, max_results=max_comments)

            if raw is None or raw.empty:
                status.warning("No comments returned from API")
                st.stop()
            df = prepare_df_for_display(raw)
            # continue to sentiment/emotion below
        except Exception as e:
            status.error(f"Error fetching comments: {e}")
            st.stop()

    # -----------------------
    # TWITTER BRANCH (placeholder)
    elif platform == "Twitter":
        from src.data_twitter import fetch_twitter_comments
        status.info("Fetching Twitter replies...")
        raw = fetch_twitter_comments(input_url)

        if raw.empty:
            status.warning("No Twitter replies found.")
            st.stop()

        df = prepare_df_for_display(raw)


    # -----------------------
    # INSTAGRAM BRANCH (placeholder)
    # -----------------------
    elif platform == "Instagram":
        from src.data_instagram import fetch_instagram_comments
        status.info("Fetching Instagram comments...")
        raw = fetch_instagram_comments(input_url)

        if raw.empty:
            status.warning("No Instagram comments found (public posts only).")
            st.stop()

        df = prepare_df_for_display(raw)


    # -----------------------
    # SENTIMENT SELECTION (ALWAYS RUNS BEFORE EMOTIONS)
    # -----------------------
    try:
        if model_choice == "VADER" and add_vader_to_df is not None:
            df = add_vader_to_df(df)
            try:
                st.sidebar.write("VADER avg compound:", round(df["vader_compound"].mean(), 4))
            except Exception:
                pass
            df["sentiment"] = df.get("vader_label", df.get("sentiment", "neutral"))
            df["sentiment_score"] = df.get("vader_compound", df.get("sentiment_score", 0.0))

        elif model_choice == "TextBlob (default)":
            # already applied in prepare_df_for_display()
            df["sentiment"] = df.get("sentiment", "neutral")
            df["sentiment_score"] = df.get("sentiment_score", 0.0)

    except Exception as e:
        status.error(f"Sentiment failed: {e}")

    # -----------------------
    # EMOTION SELECTION (RUNS AFTER SENTIMENT)
    # -----------------------
    if use_emotions:
        nrc_cols = ["anger","anticipation","disgust","fear","joy","sadness","surprise","trust"]
        emo_added = False

        # TextBlob + VADER -> NRC lexicon
        if model_choice in ["TextBlob (default)", "VADER"]:
            try:
                from src.emotion_analysis import add_emotion_columns
                # only add if not present
                if not set(nrc_cols).intersection(df.columns):
                    df = add_emotion_columns(df)
                emo_added = bool(set(nrc_cols).intersection(df.columns))
                if emo_added:
                    status.info("NRC emotions added.")
            except Exception as e:
                status.warning(f"NRC emotion extraction failed: {e}")

        # If nothing was added, create zero columns to avoid downstream crashes
        if not emo_added:
            for col in nrc_cols:
                if col not in df.columns:
                    df[col] = 0.0
            if "dominant_emotion" not in df.columns:
                df["dominant_emotion"] = "none"
            status.info("No emotion model available — using zeroed NRC columns as placeholder.")
    else:
        # emotions disabled by user -> create placeholder columns so charts don't break
        nrc_cols = ["anger","anticipation","disgust","fear","joy","sadness","surprise","trust"]
        for col in nrc_cols:
            if col not in df.columns:
                df[col] = 0.0
        if "dominant_emotion" not in df.columns:
            df["dominant_emotion"] = "none"
        status.info("Emotion analysis disabled — placeholder emotion columns added.")

    # Optional: compare TextBlob vs VADER if both available
    try:
        if model_choice == "VADER" and "vader_label" in df.columns and "sentiment" in df.columns:
            agree_pct = (df["sentiment"] == df["vader_label"]).mean()
            st.sidebar.metric("TB vs VADER agreement", f"{agree_pct:.1%}")
    except Exception:
        pass

    # save and signal complete
    st.session_state.last_df = df
    status.success(f"Fetched {len(df)} comments and analyzed sentiments.")

# -----------------------
# Show analytics if we have a df
# -----------------------
df = st.session_state.last_df
if not df.empty:
    # top stats
    with top_stats[0]:
        st.metric("Comments", f"{len(df)}")
    with top_stats[1]:
        avg_sent = round(df['sentiment_score'].mean(),4) if 'sentiment_score' in df.columns else "N/A"
        st.metric("Avg Sentiment", avg_sent)
    with top_stats[2]:
        st.metric("Top Likes", int(df['like_count'].max() or 0))

    # visuals
    with viz_col1:
        st.subheader("Sentiment Overview")
        st.plotly_chart(plot_sentiment_bar(df), use_container_width=True)
        st.plotly_chart(plot_sentiment_pie(df), use_container_width=True)

        # timeseries (if available)
        ts_fig = timeseries_sentiment(df)
        if ts_fig is not None:
            st.subheader("Sentiment Over Time")
            st.plotly_chart(ts_fig, use_container_width=True)

    with viz_col2:
        st.subheader("Likes vs Sentiment")
        st.plotly_chart(plot_likes_vs_sentiment(df), use_container_width=True)

        st.subheader("Word Cloud")
        text = " ".join(df['text'].dropna().astype(str))
        wc_fig = make_wordcloud_figure(text, width=600, height=300)
        st.pyplot(wc_fig)

    st.markdown("### Comments")

    # sorting
    if sort_opt == "Most liked":
        df = df.sort_values(by='like_count', ascending=False)
    elif sort_opt == "Most recent" and 'published_at' in df.columns:
        df = df.sort_values(by='published_at', ascending=False)
    elif sort_opt == "Most positive":
        df = df.sort_values(by='sentiment_score', ascending=False)
    elif sort_opt == "Most negative":
        df = df.sort_values(by='sentiment_score', ascending=True)

    show_df = df.head(n_display)

    import html

    # -------- A. safe formatter --------
    def safe_format_comment_card(row):
        author    = html.escape(str(row.get('author', '')))
        likes     = html.escape(str(row.get('like_count', 0)))
        text      = html.escape(str(row.get('text', '')))
        published = html.escape(str(row.get('publishedAt', '')))

        # ---------- emotion values (escape everything) ----------
        emotions = {
            "joy": row.get("joy", 0),
            "anger": row.get("anger", 0),
            "fear": row.get("fear", 0),
            "sadness": row.get("sadness", 0),
            "disgust": row.get("disgust", 0),
            "surprise": row.get("surprise", 0),
            "trust": row.get("trust", 0),
            "anticipation": row.get("anticipation", 0)
        }

        # Convert to safe string for tooltip
        emo_string = html.escape(
            "\n".join([f"{k}: {v}" for k, v in emotions.items()])
        )

        return f"""
        <div class="card" title="{emo_string}">
            <div class="card-header">
                <span class="author">@{author}</span>
                <span class="likes">👍 {likes}</span>
            </div>
            <div class="card-body">
                <p class="comment-text">{text}</p>
                <p class="meta">{published}</p>
            </div>
        </div>
        """

    # -------- B. build scrollable container --------
    cards = '<div class="scroll-area">'
    for _, row in show_df.iterrows():
        cards += safe_format_comment_card(row)
    cards += '</div>'

    # -------- C. full HTML for iframe --------
    full_html = f"""
    <!doctype html>
    <html>
    <head>
    <meta charset="utf-8">
    <style>
    :root {{
      --bg: rgba(20,28,38,0.95);
      --card-bg: rgba(12,18,26,0.85);
      --accent: #7de9ff;
      --muted: #89cfff;
      --text: #e6fbff;
    }}

    body {{
      margin: 0;
      padding: 12px;
      background: transparent;
      font-family: Inter, system-ui, -apple-system, "Segoe UI", Roboto, "Helvetica Neue", Arial;
    }}

    .scroll-area {{
        max-height: 600px;        /* SCROLL AREA HEIGHT */
        overflow-y: auto;
        padding-right: 10px;
    }}

    .scroll-area::-webkit-scrollbar {{
        width: 8px;
    }}

    .scroll-area::-webkit-scrollbar-thumb {{
        background: rgba(0, 255, 255, 0.35);
        border-radius: 10px;
    }}

    .scroll-area::-webkit-scrollbar-track {{
        background: rgba(255, 255, 255, 0.08);
    }}

    .card {{
        background: var(--card-bg);
        border-radius: 12px;
        padding: 14px 16px;
        margin-bottom: 14px;
        border: 1px solid rgba(0, 225, 255, 0.15);
        box-shadow: 0 6px 18px rgba(0,0,0,0.45);
        transition: transform .16s ease, box-shadow .16s ease;
    }}

    .card:hover {{
        transform: translateY(-4px);
        box-shadow: 0 12px 30px rgba(0,225,255,0.18);
    }}

    .card-header {{
        display:flex;
        justify-content:space-between;
        align-items:center;
        margin-bottom:10px;
        gap: 12px;
    }}

    .author {{
        color: #9feaff;
        font-weight: 700;
        font-size: 14px;
    }}

    .likes {{
        color: var(--muted);
        font-weight: 600;
        font-size: 13px;
    }}

    .comment-text {{
        color: var(--text);
        font-size: 15px;
        line-height: 1.45;
    }}

    .meta {{
        margin-top: 8px;
        color: #79bfff;
        font-size: 12px;
    }}
    
    </style>
    </head>
    <body>
      {cards}
    </body>
    </html>
    """

    # -------- D. render clean --------
    components.html(full_html, height=650, scrolling=False)

    # --- Hashtag & Keyword Analysis ---
    st.markdown("### Hashtag & Keyword Insights")

    # HASHTAGS
    hashtags = get_hashtag_counts(df)

    if len(hashtags) > 0:
        top_tags = hashtags.most_common(20)
        tags_df = pd.DataFrame(top_tags, columns=["hashtag","count"])

        st.subheader("Top Hashtags")
        fig_tags = px.bar(tags_df, x="hashtag", y="count",
                          title="Most Frequent Hashtags",
                          template="plotly_dark")
        st.plotly_chart(fig_tags, use_container_width=True)
    else:
        st.info("No hashtags found in comments.")

    # KEYWORDS
    keywords = get_keyword_counts(df, top_n=20)

    if len(keywords) > 0:
        kw_df = pd.DataFrame(keywords, columns=["keyword","count"])

        st.subheader("Top Keywords")
        fig_kw = px.bar(kw_df, x="keyword", y="count",
                        title="Most Frequent Keywords",
                        template="plotly_dark")
        st.plotly_chart(fig_kw, use_container_width=True)
    else:
        st.info("No meaningful keywords found.")

    # -------------------------------
    #  EMOTION ANALYSIS (AGGREGATES)
    # -------------------------------
    st.markdown("## 😃 Emotion Analysis")

    emotion_cols = [
        "anger","disgust","fear","joy","sadness","surprise","trust","anticipation"
    ]

    # Only use columns that actually exist (NRC or transformer emotions will be present as appropriate)
    available_emotions = [c for c in emotion_cols if c in df.columns]

    if len(available_emotions) == 0:
        st.info("No emotion data available for the selected model.")
    else:
        emotion_sums = df[available_emotions].sum().sort_values(ascending=False)
        emo_df = pd.DataFrame({"emotion": emotion_sums.index, "score": emotion_sums.values})

        fig_emo = px.bar(
            emo_df,
            x="emotion",
            y="score",
            title="Emotion Intensity Across Comments",
            template="plotly_dark"
        )

        st.plotly_chart(fig_emo, use_container_width=True)

        # dominant emotion pie chart (only if column exists)
        if "dominant_emotion" in df.columns:
            dominant_counts = df["dominant_emotion"].value_counts()
            fig_dom = px.pie(
                values=dominant_counts.values,
                names=dominant_counts.index,
                title="Dominant Emotion Distribution",
                template="plotly_dark"
            )
            st.plotly_chart(fig_dom, use_container_width=True)

    # Save to DB action
    if save_to_db:
        try:
            status.info("Saving results to DB...")
            # ensure column names match DB schema
            df_to_save = df.copy()
            # rename local columns to DB columns expected by insert_comments
            if 'text' in df_to_save.columns and 'comment' in df_to_save.columns:
                df_to_save = df_to_save.rename(columns={'comment':'text'})
            if 'like_count' not in df_to_save.columns and 'likes' in df_to_save.columns:
                df_to_save = df_to_save.rename(columns={'likes':'like_count'})

            # ensure required columns exist
            for c in ['comment_id','video_id','author','text','published_at','like_count']:
                if c not in df_to_save.columns:
                    df_to_save[c] = None

            create_comments_table()
            insert_comments(df_to_save)
            # ---  Update VADER columns if they exist ---
            if "vader_label" in df_to_save.columns:
                from src.db_utils import get_connection
                conn = get_connection()
                cur = conn.cursor()
                for _, r in df_to_save.iterrows():
                    cur.execute("""
                        UPDATE youtube_comments
                        SET vader_compound=%s, vader_positive=%s, vader_neutral=%s, vader_negative=%s, vader_label=%s
                        WHERE comment_id=%s
                    """, (
                        r.get("vader_compound"),
                        r.get("vader_positive"),
                        r.get("vader_neutral"),
                        r.get("vader_negative"),
                        r.get("vader_label"),
                        r.get("comment_id"),
                    ))
                conn.commit()
                cur.close()
                conn.close()
                status.info("VADER results saved to DB.")

            status.success("Saved analysis to DB ")
        except Exception as e:
            status.error(f"DB Save failed: {e}")

else:
    st.info("No analysis loaded yet. Paste a content URL in the left and press Fetch & Analyze.")

# ---------------------------------------------------------
# Export Section (Fixed)
# ---------------------------------------------------------
st.markdown("---")
st.subheader("Export Analyzed Data")

# Use session_state df if available
if "last_df" in st.session_state and not st.session_state.last_df.empty:
    df_export = st.session_state.last_df.copy()

    # Convert timezone-aware datetime columns to naive (Excel-safe)
    for col in df_export.select_dtypes(include=["datetimetz"]).columns:
        df_export[col] = df_export[col].dt.tz_localize(None)

    # Prepare files in memory
    csv = df_export.to_csv(index=False).encode('utf-8')
    excel_buffer = io.BytesIO()
    df_export.to_excel(excel_buffer, index=False, engine='xlsxwriter')

    col1, col2 = st.columns(2)
    with col1:
        st.download_button(
            label="Download as CSV",
            data=csv,
            file_name="youtube_comments_sentiment.csv",
            mime="text/csv"
        )

    with col2:
        st.download_button(
            label="Download as Excel",
            data=excel_buffer.getvalue(),
            file_name="youtube_comments_sentiment.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
else:
    st.info("No data available to export yet.")
