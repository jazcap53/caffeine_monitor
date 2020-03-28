import json
from datetime import datetime
import pytest


@pytest.fixture(scope='function')
def c_mon(tmpdir):
    log_file = tmpdir.join('caffeine_test.log')
    json_file = tmpdir.join('caffeine_test.json')
    cur_datetime = datetime.now()
    fmt_cur_datetime = cur_datetime.strftime('%Y-%m-%d_%H:%M')
    log_file.write(f'48 mg added: level is 48.0 at {fmt_cur_datetime}')
    json_data = {"time": fmt_cur_datetime, "level": 48.0}
    json.dump(json_data, json_file)
    return log_file, json_file
