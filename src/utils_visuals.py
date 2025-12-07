import io
import pandas as pd
import plotly.express as px
from wordcloud import WordCloud
import matplotlib.pyplot as plt

CYBER_COLORS = {
    "positive": "#00E1FF",  # cyan
    "negative": "#FF004F",  # red accent (used lightly)
    "neutral":  "#FFD300"   # yellow
}

def plot_sentiment_bar(df):
    counts = df['sentiment'].value_counts().reindex(['positive','neutral','negative']).fillna(0)
    fig = px.bar(
        x=counts.index, y=counts.values,
        labels={'x':'Sentiment','y':'Count'},
        title='Sentiment Distribution (Bar)',
        template='plotly_dark'
    )
    fig.update_traces(marker_color=[CYBER_COLORS.get(x,'#00E1FF') for x in counts.index])
    return fig

def plot_sentiment_pie(df):
    counts = df['sentiment'].value_counts()
    fig = px.pie(values=counts.values, names=counts.index, title='Sentiment Distribution (Pie)', template='plotly_dark')
    return fig

def plot_likes_vs_sentiment(df):
    # jitter the x position for categories to show distribution
    fig = px.strip(df, x='sentiment', y='like_count', hover_data=['author','text'],
                   title='Likes vs Sentiment (Scatter)', template='plotly_dark')
    return fig

def timeseries_sentiment(df):
    if 'published_at' not in df.columns:
        return None
    df = df.copy()
    df['published_at'] = pd.to_datetime(df['published_at'], errors='coerce')
    ts = df.set_index('published_at').resample('D').sentiment_score.mean().dropna()
    if ts.empty:
        return None
    fig = px.line(ts, x=ts.index, y=ts.values, labels={'x':'Date','y':'Avg Sentiment Score'}, title='Sentiment Over Time', template='plotly_dark')
    return fig

def make_wordcloud_figure(text, width=800, height=400):
    if not isinstance(text, str) or text.strip()=="":
        fig, ax = plt.subplots(figsize=(8,4), facecolor='black')
        ax.text(0.5,0.5,"No text to generate wordcloud", color="white", ha="center")
        ax.axis("off")
        return fig
    wc = WordCloud(width=width, height=height, background_color="black",
                   colormap=None, prefer_horizontal=0.9,
                   regexp=r"\w[\w']+").generate(text)
    fig, ax = plt.subplots(figsize=(width/100, height/100), facecolor='black')
    ax.imshow(wc, interpolation='bilinear')
    ax.axis("off")
    return fig


   
def format_comment_card(row):
    return f"""
    <div class="card">
        <div class="card-header">
            <span class="author">{row.get('author','unknown')}</span>
            <span class="likes">👍 {row.get('like_count',0)}</span>
        </div>
        <div class="card-body">
            <p class="comment-text">{row.get('text','')}</p>
            <p class="meta">{row.get('published_at')}</p>
        </div>
    </div>
    """




