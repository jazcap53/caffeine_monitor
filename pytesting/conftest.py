# file: conftest.py

import io
import json
from datetime import datetime
import os
import pytest
from pytest_mock import MockerFixture
from caffeine_monitor.src.utils import read_config_file, set_up
from pathlib import Path
import tempfile
from pytesting.temp_file_wrapper import TempFileWrapper
# TODO: introduces coupling to the sut; find another solution
from caffeine_monitor.src.utils import read_config_file, CONFIG_FILENAME


config = read_config_file(CONFIG_FILENAME)
temp_dir = os.path.dirname(config['pytesting']['log_file'])


# @pytest.fixture(scope='session')
# def temp_log_file():
#     with tempfile.NamedTemporaryFile(suffix='.log') as f:
#         yield TempFileWrapper(f)


@pytest.fixture(scope='session')
def temp_json_log_files():
    with tempfile.NamedTemporaryFile(suffix='.log') as log_file, \
         tempfile.NamedTemporaryFile(suffix='.json') as json_file, \
         tempfile.NamedTemporaryFile(suffix='.json', prefix='future_') as json_future_file:
        yield TempFileWrapper(log_file), TempFileWrapper(json_file), TempFileWrapper(json_future_file)


# @pytest.fixture
# def config_ini_mocked(mocker):
#     temp_log_file = tempfile.NamedTemporaryFile(suffix='.log', dir=temp_dir, delete=True)
#     temp_json_file = tempfile.NamedTemporaryFile(suffix='.json', dir=temp_dir, delete=True)
#     temp_json_future_file = tempfile.NamedTemporaryFile(suffix='.json', dir=temp_dir, delete=True)
#
#     config_mock = {
#         'pytesting': {
#             'log_file': TempFileWrapper(temp_log_file),
#             'json_file': TempFileWrapper(temp_json_file),
#             'json_file_future': TempFileWrapper(temp_json_future_file)
#         },
#         'tests': {
#             'log_file': TempFileWrapper(temp_log_file),
#             'json_file': TempFileWrapper(temp_json_file),
#             'json_file_future': TempFileWrapper(temp_json_future_file)
#         }
#     }
#
#     mocker.patch('caffeine_monitor.src.utils.read_config_file', return_value=config_mock)
#
#     yield
#
#     # temp_log_file.close()
#     # temp_json_file.close()
#     # temp_json_future_file.close()
#     # os.remove(temp_log_file.name)
#     # os.remove(temp_json_file.name)
#     # os.remove(temp_json_future_file.name)


@pytest.fixture(scope='session')
def config_ini_mocked(mocker, temp_json_log_files):
    temp_log_file, temp_json_file, temp_json_future_file = temp_json_log_files

    pytesting_log_file = tempfile.NamedTemporaryFile(suffix='.log', dir='pytesting', delete=False)
    pytesting_json_file = tempfile.NamedTemporaryFile(suffix='.json', dir='pytesting', delete=False)
    pytesting_json_future_file = tempfile.NamedTemporaryFile(suffix='.json', dir='pytesting', delete=False, prefix='future_')

    config_mock = {
        'pytesting': {
            'log_file': pytesting_log_file.name,
            'json_file': pytesting_json_file.name,
            'json_file_future': pytesting_json_future_file.name
        },
        'test': {
            'log_file': str(temp_log_file.tempfile.name),
            'json_file': str(temp_json_file.tempfile.name),
            'json_file_future': str(temp_json_future_file.tempfile.name)
        }
    }

    mocker.patch('caffeine_monitor.src.utils.read_config_file', return_value=config_mock)

    yield

    # Clean up the temporary files
    for temp_file in [temp_log_file, temp_json_file, temp_json_future_file]:
        temp_file.reset()

    # Clean up the pytesting temporary files
    pytesting_log_file.close()
    pytesting_json_file.close()
    pytesting_json_future_file.close()
    os.unlink(pytesting_log_file.name)
    os.unlink(pytesting_json_file.name)
    os.unlink(pytesting_json_future_file.name)


@pytest.fixture
def files_mocked(mocker: MockerFixture):
    open_mock = mocker.patch('builtins.open', new_callable=mocker.mock_open,
                             read_data='Start of log file')

    json_load_mock = mocker.patch('json.load')
    json_dump_mock = mocker.patch('json.dump')

    def json_dump_side_effect(data, file_handle):
        file_handle.write(json.dumps(data))

    json_dump_mock.side_effect = json_dump_side_effect

    def json_load_side_effect():
        return {"time": (dt_now := datetime.now().strftime('%Y-%m-%d_%H:%M')), "level": 0.0}

    json_load_mock.side_effect = [
        json_load_side_effect(),
        []
    ]

    open_mock.side_effect = [
        mocker.DEFAULT,  # For the log file
        mocker.DEFAULT,  # For read_file
        mocker.DEFAULT,  # For read_future_file
    ]

    yield open_mock, json_load_mock, json_dump_mock

    json_load_mock.reset_mock(side_effect=True)
    json_dump_mock.reset_mock(side_effect=True)
