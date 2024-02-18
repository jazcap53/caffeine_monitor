import json
from datetime import datetime
import pytest
from src.caffeine_monitor import CaffeineMonitor
from argparse import Namespace

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

    return FakeFile()

@pytest.fixture(scope='function')
def test_files(tmpdir, fake_file):
    log_file = fake_file
    json_file = fake_file
    json_future_file = fake_file
    a_datetime = datetime(2020, 4, 1, 12, 51)
    fmt_a_datetime = a_datetime.strftime('%Y-%m-%d_%H:%M')
    json_data = {"time": fmt_a_datetime, "level": 48.0}
    json_file.content = json.dumps(json_data)
    return log_file, json_file, json_future_file

@pytest.fixture(scope='function')
def cm(test_files):
    log_file = test_files[0]
    json_file = test_files[1]
    json_future_file = test_files[2]
    first_run = True
    fake_ags = Namespace(mg=0, mins=0, bev='coffee')
    yield CaffeineMonitor(log_file, json_file, json_future_file, first_run, fake_ags)

@pytest.fixture
def nmsp():
    return Namespace(mg=100, mins=180, bev='coffee')
