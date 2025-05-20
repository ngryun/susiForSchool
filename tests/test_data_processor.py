import math
import pandas as pd
from pathlib import Path
import pytest

from data_processor import read_input, compute_stats, compute_additional_stats


def test_read_input(monkeypatch):
    raw = pd.DataFrame([
        ['univ1', 'typeA', 'dept1', 1.1, '합격', 3.2],
        ['univ2', 'typeB', 'dept2', 2.2, '불합격', 3.0],
        [None, 'typeC', 'dept3', 4.0, '합격', 2.7],
        ['univ4', 'typeD', 'dept4', None, '불합격', None],
        ['univ5', 'typeE', 'dept5', 4.5, None, 2.4],
    ])
    called = {}

    def fake_read_excel(path, header=None, skiprows=None, usecols=None, engine=None):
        called['header'] = header
        called['skiprows'] = skiprows
        called['usecols'] = usecols
        called['engine'] = engine
        return raw.copy()

    monkeypatch.setattr(pd, 'read_excel', fake_read_excel)

    df = read_input(Path('dummy.xlsx'))

    assert called['skiprows'] == 2
    assert called['usecols'] == 'F,L,J,R,U,AE'
    assert list(df.columns) == ['univ', 'subtype', 'dept', 'conv_grade', 'result', 'all_subj_grade']
    assert len(df) == 2
    assert df['univ'].isna().sum() == 0
    assert df['result'].isna().sum() == 0


def sample_df():
    return pd.DataFrame({
        'result': ['합격', '합격', '불합격', '충원합격', '충원합격'],
        'conv_grade': [1.0, 2.0, 3.0, 2.0, 2.5],
    })


def test_compute_stats():
    df = sample_df()
    stats = compute_stats(df, 'conv_grade')

    assert stats['total_count'] == 5
    assert stats['all_pass_count'] == 4
    assert stats['all_pass_rate'] == '80.0%'
    assert stats['all_pass_min'] == 1.0
    assert stats['all_pass_max'] == 2.5
    assert stats['pass_count'] == 2
    assert stats['pass_rate'] == '40.0%'
    assert stats['pass_min'] == 1.0
    assert stats['pass_max'] == 2.0
    assert stats['waitlist_count'] == 2
    assert stats['waitlist_rate'] == '40.0%'
    assert stats['waitlist_min'] == 2.0
    assert stats['waitlist_max'] == 2.5
    assert stats['fail_count'] == 1
    assert stats['pass_mean'] == pytest.approx(1.5)
    assert stats['waitlist_mean'] == pytest.approx(2.25)
    assert stats['all_pass_mean'] == pytest.approx(1.875)


def test_compute_additional_stats():
    df = sample_df()
    stats = compute_additional_stats(df, 'conv_grade')

    pass_stats = stats['합격']
    assert pass_stats['count'] == 2
    assert pass_stats['min'] == 1.0
    assert pass_stats['max'] == 2.0
    assert pass_stats['mean'] == pytest.approx(1.5)
    assert pass_stats['median'] == pytest.approx(1.5)
    assert pass_stats['q1'] == pytest.approx(1.25)
    assert pass_stats['q3'] == pytest.approx(1.75)
    assert pass_stats['std'] == pytest.approx(math.sqrt(0.5))
    assert pass_stats['cv'] == pytest.approx(math.sqrt(0.5) / 1.5 * 100)

    fail_stats = stats['불합격']
    assert fail_stats['count'] == 1
    assert fail_stats['min'] == 3.0
    assert fail_stats['max'] == 3.0
    assert fail_stats['mean'] == 3.0
    assert math.isnan(fail_stats['std'])

    wait_stats = stats['충원합격']
    assert wait_stats['count'] == 2
    assert wait_stats['min'] == 2.0
    assert wait_stats['max'] == 2.5
    assert wait_stats['mean'] == pytest.approx(2.25)
    assert wait_stats['median'] == pytest.approx(2.25)
    assert wait_stats['q1'] == pytest.approx(2.125)
    assert wait_stats['q3'] == pytest.approx(2.375)
    assert wait_stats['std'] == pytest.approx(math.sqrt(0.125))
    assert wait_stats['cv'] == pytest.approx(math.sqrt(0.125) / 2.25 * 100)
