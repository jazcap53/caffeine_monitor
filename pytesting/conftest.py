import json
from datetime import datetime
import pytest
from src.caffeine_monitor import CaffeineMonitor
from argparse import Namespace


@pytest.fixture
def fake_file():
    class FakeFile:
        def __init__(self):
            self.log_contents = ""
            self.json_contents = ""
            self.json_future_contents = ""

        def write(self, data):
            self.log_contents += data

        def dump(self, data):
            self.json_contents += data

    return FakeFile()


@pytest.fixture(scope='function')
def test_files(tmpdir, fake_file):
    log_file = fake_file  # tmpdir.join('empty_caffeine_test.log')
    json_file = fake_file  # tmpdir.join('empty_caffeine_test.json')
    json_future_file = fake_file
    a_datetime = datetime(2020, 4, 1, 12, 51)
    fmt_a_datetime = a_datetime.strftime('%Y-%m-%d_%H:%M')
    # with open(log_file, 'w') as l_file, open(json_file, 'w') as j_file:
    #     l_file.write(f'48 mg added: level is 48.0 at {fmt_a_datetime}')
    #     json_data = {"time": fmt_a_datetime, "level": 48.0}
    #     json.dump(json_data, j_file)
    # return log_file.strpath, json_file.strpath
    return log_file, json_file, json_future_file


@pytest.fixture(scope='function')
def cm(test_files):
    log_file = test_files[0]
    json_file = test_files[1]
    json_future_file = test_files[2]
    first_run = True
    fake_ags = Namespace(mg=0, mins=0, bev='coffee')
    # with open(json_file, 'r+') as j_file:
    #     yield CaffeineMonitor(fake_file, fake_ags)
    yield CaffeineMonitor(log_file, json_file, json_future_file, first_run, fake_ags)