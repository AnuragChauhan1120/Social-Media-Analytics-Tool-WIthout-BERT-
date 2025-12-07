import re
import pandas as pd
from collections import Counter
import nltk

# download stopwords once
try:
    nltk.data.find('corpora/stopwords')
except:
    nltk.download('stopwords')

from nltk.corpus import stopwords
stop_words = set(stopwords.words("english"))

def extract_hashtags(text):
    if not isinstance(text, str):
        return []
    return re.findall(r"#\w+", text.lower())

def extract_keywords(text):
    if not isinstance(text, str):
        return []
    # remove non letters
    text = re.sub(r"[^a-zA-Z\s]", " ", text).lower()
    words = [w for w in text.split() if w not in stop_words and len(w) > 2]
    return words

def get_hashtag_counts(df):
    all_tags = []
    for t in df["text"].dropna():
        all_tags.extend(extract_hashtags(t))
    return Counter(all_tags)

def get_keyword_counts(df, top_n=20):
    all_words = []
    for t in df["text"].dropna():
        all_words.extend(extract_keywords(t))
    return Counter(all_words).most_common(top_n)
