import json
from datetime import datetime
import pytest
from src.caffeine_monitor import CaffeineMonitor
from argparse import Namespace


@pytest.fixture(scope='function')
def test_files(tmpdir):
    log_file = tmpdir.join('empty_caffeine_test.log')
    json_file = tmpdir.join('empty_caffeine_test.json')
    a_datetime = datetime(2020, 4, 1, 12, 51)
    fmt_a_datetime = a_datetime.strftime('%Y-%m-%d_%H:%M')
    with open(log_file, 'w') as l_file, open(json_file, 'w') as j_file:
        l_file.write(f'48 mg added: level is 48.0 at {fmt_a_datetime}')
        json_data = {"time": fmt_a_datetime, "level": 48.0}
        json.dump(json_data, j_file)
    return log_file.strpath, json_file.strpath


@pytest.fixture(scope='function')
def cm(test_files):
    json_file = test_files[1]
    fake_ags = Namespace(mg=0, mins=0)
    with open(json_file, 'r+') as j_file:
        yield CaffeineMonitor(j_file, fake_ags)
