from nrclex import NRCLex
import pandas as pd

def get_emotions(text):
    if not isinstance(text, str):
        return {}

    emo = NRCLex(text)
    return emo.raw_emotion_scores  # dictionary of emotions

def add_emotion_columns(df):
    df = df.copy()

    emotion_names = [
        "anger", "anticipation", "disgust", "fear",
        "joy", "sadness", "surprise", "trust"
    ]

    for col in emotion_names:
        df[col] = 0

    for idx, text in df["text"].fillna("").items():
        scores = get_emotions(text)
        for emotion in emotion_names:
            df.at[idx, emotion] = scores.get(emotion, 0)

    # dominant emotion
    df["dominant_emotion"] = df[emotion_names].idxmax(axis=1)

    return df
