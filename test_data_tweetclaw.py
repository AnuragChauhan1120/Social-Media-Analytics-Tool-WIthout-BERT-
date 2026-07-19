from src.data_tweetclaw import load_tweetclaw_export


class UploadedFile:
    def __init__(self, content: bytes):
        self.content = content

    def getvalue(self) -> bytes:
        return self.content


def test_csv_skips_rows_with_missing_text():
    uploaded_file = UploadedFile(
        b"id,text,username,like_count\n1,Useful update,alice,4\n2,,bob,2\n"
    )

    result = load_tweetclaw_export(uploaded_file, "tweets.csv")

    assert result["comment_id"].tolist() == ["1"]
    assert result["text"].tolist() == ["Useful update"]
    assert result["like_count"].tolist() == [4]


def test_json_normalizes_nested_author():
    uploaded_file = UploadedFile(
        b'{"data":[{"id":"42","text":"Hello","author":{"username":"alice"}}]}'
    )

    result = load_tweetclaw_export(uploaded_file, "tweets.json")

    assert result["author"].tolist() == ["alice"]
