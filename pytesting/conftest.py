# file: conftest.py

import json
from datetime import datetime
import pytest
from caffeine_monitor.src.caffeine_monitor import CaffeineMonitor
from caffeine_monitor.src.utils import read_config_file
from argparse import Namespace
from pathlib import Path


@pytest.fixture
def fake_file():
    class FakeFile:
        def __init__(self, initial_content=''):
            self.content = initial_content
            self.position = 0

        def read(self, size=None):
            if size is None:
                result = self.content[self.position:]
                self.position = len(self.content)
            else:
                result = self.content[self.position:self.position + size]
                self.position += size
            return result

        def write(self, data):
            self.content += data

        def seek(self, offset, whence=0):
            if whence == 0:
                self.position = offset
            elif whence == 1:
                self.position += offset
            elif whence == 2:
                self.position = len(self.content) + offset

        def truncate(self, size=0):
            self.content = self.content[:size]

        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc_val, exc_tb):
            pass

    return FakeFile()


@pytest.fixture(scope='session')
def pytesting_files():
    config = read_config_file('src/caffeine.ini')
    log_filename = Path(config['pytesting']['log_file'])
    json_filename = Path(config['pytesting']['json_file'])
    json_future_filename = Path(config['pytesting']['json_file_future'])

    with (log_filename.open('a+') as log_file, json_filename.open('r+') as json_file,
          json_future_filename.open('r+') as json_future_file):
        yield log_file, json_file, json_future_file


# @pytest.fixture(scope='function')
# def test_files(tmpdir, fake_file):
#     log_file = fake_file
#     json_file = fake_file
#     json_future_file = fake_file
#     a_datetime = datetime(2020, 4, 1, 12, 51)
#     fmt_a_datetime = a_datetime.strftime('%Y-%m-%d_%H:%M')
#     json_data = {"time": fmt_a_datetime, "level": 48.0}
#     json_file.content = json.dumps(json_data)
#     return log_file, json_file, json_future_file


# @pytest.fixture
# def cm_obj(pytesting_files, request, mg=0, mins=0, bev='coffee'):
#     log_file, json_file, json_future_file = pytesting_files
#     args = Namespace(mg=mg, mins=mins, bev=bev)
#
#     cm = CaffeineMonitor(log_file, json_file, json_future_file, True, args)
#     yield cm


# @pytest.fixture
# def nmsp():
#     return Namespace(mg=100, mins=180, bev='coffee')


# ==============
# SAVING FOR (possible, unlikely) USE IN TESTS

# @pytest.mark.parametrize('cm', [
#     Namespace(mg=100, mins=20, bev='coffee'),
#     Namespace(mg=200, mins=10, bev='soda'),
# ], indirect=True)
