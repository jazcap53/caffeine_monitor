# file: conftest.py

import json
from datetime import datetime
import pytest
from pytest_mock import MockerFixture
from caffeine_monitor.src.utils import read_config_file, set_up
from pathlib import Path


# TODO: PHASE OUT THIS FIXTURE
@pytest.fixture(scope='session')
def pytesting_files():
    config = read_config_file('src/caffeine.ini')
    log_filename = Path(config['pytesting']['log_file'])
    json_filename = Path(config['pytesting']['json_file'])
    json_future_filename = Path(config['pytesting']['json_file_future'])

    with (log_filename.open('a+') as log_file, json_filename.open('r+') as json_file,
          json_future_filename.open('r+') as json_future_file):
        yield log_file, json_file, json_future_file


# TODO: PHASE OUT THIS FIXTURE
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


# TODO: BREAK INTO 2 FIXTURES, 1 THAT MOCKS THE .INI FILE AND 1 THAT YIELDS MOCKED FILES ???
@pytest.fixture
def pytesting_files_scratch_mocked(mocker):
    # Mock the config
    config_mock = {'pytesting': {'log_file': 'mock_log.log', 'json_file': 'mock.json', 'json_file_future': 'mock_future.json'}}
    mocker.patch('caffeine_monitor.src.utils.read_config_file', return_value=config_mock)

    log_mock = mocker.mock_open(read_data='Start of log file')
    json_mock = mocker.mock_open(read_data='{"time": "2020-01-01_00:00", "level": 0.0}')
    future_json_mock = mocker.mock_open(read_data='[]')

    mocker.patch('builtins.open', side_effect=[log_mock.return_value, json_mock.return_value, future_json_mock.return_value])

    log_mock.return_value.seek(0)
    json_mock.return_value.configure_mock(**{'write.return_value': None})
    future_json_mock.return_value.configure_mock(**{'write.return_value': None})

    return log_mock, json_mock, future_json_mock


@pytest.fixture
def config_mocked(mocker):
    config_mock = {'pytesting': {'log_file': 'mock_log.log', 'json_file': 'mock.json',
                                 'json_file_future': 'mock_future.json'}}
    mocker.patch('caffeine_monitor.src.utils.read_config_file', return_value=config_mock)


@pytest.fixture
def files_mocked(mocker: MockerFixture):
    open_mock = mocker.patch('builtins.open', new_callable=mocker.mock_open, read_data='Start of log file')

    json_load_mock = mocker.patch('json.load')

    def json_load_side_effect():
        return {"time": (dt_now := datetime.datetime.now().strftime('%Y-%m-%d_%H:%M')), "level": 0.0}

    json_load_mock.side_effect = [
        json_load_side_effect,
        []
    ]

    open_mock.side_effect = [
        mocker.DEFAULT,  # For the log file
        mocker.DEFAULT,  # For read_file
        mocker.DEFAULT,  # For read_future_file
    ]

    yield open_mock, json_load_mock

    json_load_mock.reset_mock(side_effect=True)
