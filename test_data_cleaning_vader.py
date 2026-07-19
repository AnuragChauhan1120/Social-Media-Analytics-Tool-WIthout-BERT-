import pandas as pd

from src.data_cleaning_vader import add_vader_to_df


def test_vader_module_imports_and_scores_text():
    source = pd.DataFrame({"text": ["I love this update", "I hate this failure"]})

    result = add_vader_to_df(source)

    assert result["vader_label"].tolist() == ["positive", "negative"]
    assert result["vader_compound"].iloc[0] > 0
    assert result["vader_compound"].iloc[1] < 0
