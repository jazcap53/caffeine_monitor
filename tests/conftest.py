import json
from datetime import datetime
import pytest


@pytest.fixture(scope='function')
def get_test_files(tmpdir):
    log_file = tmpdir.join('empty_caffeine_test.log')
    json_file = tmpdir.join('empty_caffeine_test.json')
    a_datetime = datetime(2020, 4, 1, 12, 51)
    fmt_a_datetime = a_datetime.strftime('%Y-%m-%d_%H:%M')
    with open(log_file, 'w') as l_file, open(json_file, 'w') as j_file:
        l_file.write(f'48 mg added: level is 48.0 at {fmt_a_datetime}')
        json_data = {"time": fmt_a_datetime, "level": 48.0}
        json.dump(json_data, j_file)
    return log_file, json_file
