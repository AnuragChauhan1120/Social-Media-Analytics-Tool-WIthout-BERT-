import psycopg2
from src.config import DB_URI

def get_connection():
    try:
        conn = psycopg2.connect(DB_URI)
        return conn
    except Exception as e:
        print("Could not connect to the database:", e)
        raise e


def create_comments_table():
    conn = get_connection()
    cur = conn.cursor()
    
    cur.execute("""
        CREATE TABLE IF NOT EXISTS youtube_comments (
            comment_id TEXT PRIMARY KEY,
            video_id TEXT,
            author TEXT,
            text TEXT,
            published_at TIMESTAMP,
            like_count INT,

            -- VADER
            vader_compound REAL,
            vader_positive REAL,
            vader_neutral REAL,
            vader_negative REAL,
            vader_label TEXT,

            -- TRANSFORMERS (sentiment)
            transformer_sentiment TEXT,
            t_positive REAL,
            t_negative REAL,
            t_neutral REAL,

            -- TRANSFORMERS (emotions)
            joy REAL,
            anger REAL,
            fear REAL,
            sadness REAL,
            disgust REAL,
            surprise REAL,
            trust REAL,
            anticipation REAL
        );

    """)

    conn.commit()
    cur.close()
    conn.close()
    print("Comments table ready in PostgreSQL")


def insert_comments(df):
    conn = get_connection()
    cur = conn.cursor()
    #df = df.rename(columns={"comment": "text"})

    for _, row in df.iterrows():
        try:
            cur.execute("""
                INSERT INTO youtube_comments (comment_id, video_id, author, text, published_at, like_count)
                VALUES (%s, %s, %s, %s, %s, %s)
                ON CONFLICT (comment_id) DO NOTHING;
            """, (
                row["comment_id"],
                row["video_id"],
                row["author"],
                row["text"],
                row["published_at"],
                row["like_count"]
            ))
        except Exception as e:
            print("Insert error:", e)

    conn.commit()
    cur.close()
    conn.close()
    print("Insert complete")
