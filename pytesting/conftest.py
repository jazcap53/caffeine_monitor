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


@pytest.fixture(scope='session')
def temp_json_log_files():
    with tempfile.NamedTemporaryFile(suffix='.log') as log_file, \
         tempfile.NamedTemporaryFile(suffix='.json') as json_file, \
         tempfile.NamedTemporaryFile(suffix='.json', prefix='future_') as json_future_file:
        yield TempFileWrapper(log_file), TempFileWrapper(json_file), TempFileWrapper(json_future_file)


@pytest.fixture(scope='session')
def temp_pytesting_json_log_files():
    with (tempfile.NamedTemporaryFile(suffix='.log') as pytesting_log_file, \
         tempfile.NamedTemporaryFile(suffix='.json') as pytesting_json_file, \
         tempfile.NamedTemporaryFile(suffix='.json', prefix='future_') as pytesting_json_future_file):
        yield (TempFileWrapper(pytesting_log_file), TempFileWrapper(pytesting_json_file),
               TempFileWrapper(pytesting_json_future_file))


@pytest.fixture(scope='session')
def config_ini_mocked(mocker, temp_json_log_files):
    tests_log_file, tests_json_file, tests_json_future_file = temp_json_log_files
    pytesting_log_file, pytesting_json_file, pytesting_json_future_file = temp_json_log_files

    config_mock = {
        'pytesting': {
            'log_file': str(pytesting_log_file.name),
            'json_file': str(pytesting_json_file.name),
            'json_file_future': str(pytesting_json_future_file.name)
        },
        'test': {
            'log_file': str(tests_log_file.tempfile.name),
            'json_file': str(tests_json_file.tempfile.name),
            'json_file_future': str(tests_json_future_file.tempfile.name)
        }
    }

    mocker.patch('caffeine_monitor.src.utils.read_config_file', return_value=config_mock)

    yield


@pytest.fixture
def files_mocked(mocker: MockerFixture):
    open_mock = mocker.patch('builtins.open', new_callable=mocker.mock_open,
                             read_data='Start of log file')

    json_load_mock = mocker.patch('json.load')
    json_dump_mock = mocker.patch('json.dump')

    def json_dump_side_effect(data, file_handle, **kwargs):
        indent = kwargs.get('indent', None)
        if indent is not None:
            file_handle.write(json.dumps(data, indent=indent))
        else:
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



# @pytest.fixture
# def files_mocked_with_initial_values(mocker: MockerFixture):
#     open_mock = mocker.patch('builtins.open', new_callable=mocker.mock_open,
#                              read_data='Start of log file')
#
#     json_load_mock = mocker.patch('json.load')
#     json_dump_mock = mocker.patch('json.dump')
#
#     def json_dump_side_effect(data, file_handle, **kwargs):
#         indent = kwargs.get('indent', None)
#         if indent is not None:
#             file_handle.write(json.dumps(data, indent=indent))
#         else:
#             file_handle.write(json.dumps(data))
#
#     json_dump_mock.side_effect = json_dump_side_effect
#
#     yield open_mock, json_load_mock, json_dump_mock



# @pytest.fixture
# def files_mocked_with_initial_values(mocker: MockerFixture):
#     open_mock = mocker.patch('builtins.open', new_callable=mocker.mock_open,
#                              read_data='Start of log file')
#
#     json_load_mock = mocker.patch('json.load')
#     json_dump_mock = mocker.patch('json.dump')
#
#     def json_dump_side_effect(data, file_handle, **kwargs):
#         indent = kwargs.get('indent', None)
#         if indent is not None:
#             file_handle.write(json.dumps(data, indent=indent))
#         else:
#             file_handle.write(json.dumps(data))
#
#     json_dump_mock.side_effect = json_dump_side_effect
#
#     yield open_mock, json_load_mock, json_dump_mock



@pytest.fixture
def files_mocked_with_initial_values(mocker: MockerFixture):
    open_mock = mocker.patch('builtins.open', new_callable=mocker.mock_open,
                             read_data='Start of log file')

    json_load_mock = mocker.patch('json.load')
    json_dump_mock = mocker.patch('json.dump')

    def json_dump_side_effect(data, file_handle, **kwargs):
        indent = kwargs.get('indent', None)
        if indent is not None:
            file_handle.write(json.dumps(data, indent=indent))
        else:
            file_handle.write(json.dumps(data))

    json_dump_mock.side_effect = json_dump_side_effect

    yield open_mock, json_load_mock, json_dump_mock


