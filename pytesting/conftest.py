# file: conftest.py

import json
from datetime import datetime
import pytest
from caffeine_monitor.src.utils import read_config_file, set_up
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


@pytest.fixture(scope='function')
def pytesting_files_scratch():
    config = read_config_file('src/caffeine.ini')
    log_filename_scratch = Path(config['pytesting']['log_file_scratch'])
    json_filename_scratch = Path(config['pytesting']['json_file_scratch'])
    json_future_filename_scratch = Path(config['pytesting']['json_file_future_scratch'])

    with (log_filename_scratch.open('w+') as log_file_scr,
          json_filename_scratch.open('w+') as json_filename_scr,
          json_future_filename_scratch.open('w+') as json_future_filename_scr):
        log_file_scr.write('Start of log file')
        log_file_scr.seek(0)
        parsed_now = datetime.now().strftime('%Y-%m-%d_%H:%M')
        empty_args = {'time': parsed_now, 'level': 0.0}
        json.dump(empty_args, json_filename_scr)
        json_filename_scr.seek(0)
        json.dump({}, json_future_filename_scr)
        json_future_filename_scr.seek(0)
        yield log_file_scr, json_filename_scr, json_future_filename_scr


# ==============
# SAVING FOR (possible) USE IN TESTS

# @pytest.mark.parametrize('cm', [
#     Namespace(mg=100, mins=20, bev='coffee'),
#     Namespace(mg=200, mins=10, bev='soda'),
# ], indirect=True)
