import pytest

from src.core.data_cleaner import clean_data
import src.core.walkin_cleaner as walkin_cleaner


def test_clean_data_walkin_dispatches_to_walkin_cleaner(monkeypatch):
    called = {'value': False}

    def fake_clean_walkin_data(df):
        called['value'] = True
        return df, {'pipeline': 'walkin'}

    monkeypatch.setattr(walkin_cleaner, 'clean_walkin_data', fake_clean_walkin_data)

    df = None
    out_df, log = clean_data(df, mode='walkin', remove_outliers=True, log_actions=False)

    assert called['value'] is True
    assert log['pipeline'] == 'walkin'
    assert out_df is None


def test_clean_data_unknown_mode_raises_value_error():
    with pytest.raises(ValueError):
        clean_data(df=None, mode='invalid-mode', remove_outliers=True, log_actions=False)
