# file: pytesting/test_utils.py

from argparse import Namespace
import src.utils
import sys
import os
import json
import pytest
from pytest_mock import mocker
from freezegun import freeze_time

from src.utils import (check_which_environment, parse_clas,
                       read_config_file, check_cla_match_env, init_storage,
                       delete_old_logfile, create_files, init_future, init_logfile,
                       set_up)
import subprocess
from src.caffeine_monitor import CaffeineMonitor
import builtins
import logging


# TODO: TDD
@pytest.mark.xfail
@pytest.mark.parametrize("mg", [50, 100, 200, 300])
@pytest.mark.parametrize("flag", ["-w", "--walltime"])
def test_parse_clas_walltime(mg, flag):
    # Arrange
    walltime = datetime.now().strftime("%H:%M")
    args = [str(mg), flag, walltime]

    # Act
    parsed_args = parse_clas(args)

    # Assert
    assert parsed_args.walltime == walltime
    assert parsed_args.mg == mg
    assert parsed_args.mins == 0


@pytest.mark.xfail
@pytest.mark.parametrize("mg", [50, 100, 200, 300])
@pytest.mark.parametrize("minutes", [15, 180, 720, -60])
@pytest.mark.parametrize("flag", ["-w", "--walltime"])
def test_parse_clas_walltime_and_minutes_mutually_exclusive(mg, minutes, flag):
    # Arrange
    walltime = datetime.now().strftime("%H:%M")
    args = [str(mg), str(minutes), flag, walltime]

    # Act and Assert
    with pytest.raises(ValueError, match=r"walltime and mins arguments are mutually exclusive"):
        parse_clas(args)


def test_bad_caff_env_value_exits(mocker):
    mocker.patch('os.environ')
    mocker.patch('sys.exit')
    os.environ['CAFF_ENV'] = 'bongo'
    __ = check_which_environment()
    assert sys.exit.called_once_with(0)


@pytest.mark.parametrize(
    "args, expected",
    [
        (["200"], {"mg": 200}),
        (["200", "360"], {"mg": 200, "mins": 360}),
        (["0", "0", "--bev", "soda"], {"mg": 0, "mins": 0, "bev": "soda"}),
        (["100", "-b", "chocolate"], {"mg": 100, "mins": 0, "bev": "chocolate"}),
        (["-b", "coffee"], {"mg": 0, "mins": 0, "bev": "coffee"}),
        (["100", "20", "--bev", "invalid"], SystemExit),
        (["-h"], SystemExit),
        (["abc"], SystemExit),  # Invalid type for mg
        (["100", "abd"], SystemExit),  # Invalid type for mins
        (["100", "-60"], SystemExit),  # Negative value for mins
        (["100", "20", "--bev", "whiskey"], SystemExit),  # Invalid beverage type
        (["100", "-b"], SystemExit),  # Missing beverage type after -b
    ],
)
def test_parse_clas(args, expected):
    if expected == SystemExit:
        with pytest.raises(SystemExit):
            parse_clas(args)
    else:
        parsed_args = parse_clas(args)
        for key, value in expected.items():
            assert getattr(parsed_args, key) == value


@pytest.mark.parametrize("env, expected_output", [
    (None, "Please export environment variable CAFF_ENV as"),
    ("pytesting", "pytesting"),
    ("prod", "prod"),
    ("devel", "devel"),
])
def test_check_which_environment(mocker, capsys, env, expected_output):
    if env is None:
        mocker.patch.dict("os.environ", {}, clear=True)
    else:
        mocker.patch.dict("os.environ", {"CAFF_ENV": env})

    if env is None:
        with pytest.raises(SystemExit):
            check_which_environment()
        out, _ = capsys.readouterr()
        assert expected_output in out
    else:
        assert check_which_environment() == expected_output


def test_read_config_file_fake(mocker):
    # Define the fake configuration file content
    fake_config_content = '''
[prod]
json_file = src/caffeine_production.json
json_file_future = src/caffeine_production_future.json
log_file = src/caffeine_production.log

[devel]
json_file = devel/caff_devel.json
json_file_future = devel/caff_devel_future.json
log_file = devel/caff_devel.log

[pytesting]
json_file = pytesting/caff_pytesting.json
json_file_future = pytesting/caff_pytesting_future.json
log_file = pytesting/caff_pytesting.log
json_file_scratch = pytesting/caff_pytesting_scratch.json
json_file_future_scratch = pytesting/caff_pytesting_future_scratch.json
log_file_scratch = pytesting/caff_pytesting_scratch.log
    '''

    # Patch the open function to return the fake configuration file content
    mock_open = mocker.patch('builtins.open', mocker.mock_open(read_data=fake_config_content))

    # Call the read_config_file function with a dummy filename
    config = read_config_file('dummy_config.ini')

    # Assert the expected configuration sections and values
    assert config.sections() == ['prod', 'devel', 'pytesting']
    assert config['prod'] == {
        'json_file': 'src/caffeine_production.json',
        'json_file_future': 'src/caffeine_production_future.json',
        'log_file': 'src/caffeine_production.log'
    }
    assert config['devel'] == {
        'json_file': 'devel/caff_devel.json',
        'json_file_future': 'devel/caff_devel_future.json',
        'log_file': 'devel/caff_devel.log'
    }
    assert config['pytesting'] == {
        'json_file': 'pytesting/caff_pytesting.json',
        'json_file_future': 'pytesting/caff_pytesting_future.json',
        'log_file': 'pytesting/caff_pytesting.log',
        'json_file_scratch': 'pytesting/caff_pytesting_scratch.json',
        'json_file_future_scratch': 'pytesting/caff_pytesting_future_scratch.json',
        'log_file_scratch': 'pytesting/caff_pytesting_scratch.log'
    }

    # Assert that the open function was called with the dummy filename
    mock_open.assert_called_once_with('dummy_config.ini', encoding='locale')  # 'locale': default system encoding


@pytest.mark.parametrize(
    "cur_env, devel_flag, pytesting_flag, expected_exit",
    [
        ("pytesting", False, True, False),
        ("pytesting", True, False, True),
        ("pytesting", False, False, True),
        ("devel", False, True, True),
        ("devel", True, False, False),
        ("devel", False, False, True),
        ("prod", False, True, True),
        ("prod", True, False, True),
        ("prod", False, False, False),
    ],
)
def test_check_cla_match_env(mocker, cur_env, devel_flag, pytesting_flag, expected_exit):
    args = mocker.MagicMock()
    args.devel = devel_flag
    args.pytesting = pytesting_flag

    mocker.patch("sys.argv", ["script.py"])
    if devel_flag:
        mocker.patch("sys.argv", ["script.py", "-d"])
    elif pytesting_flag:
        mocker.patch("sys.argv", ["script.py", "-q"])

    mock_exit = mocker.patch("sys.exit")

    check_cla_match_env(cur_env, args)

    if expected_exit:
        mock_exit.assert_called_once_with(0)
    else:
        mock_exit.assert_not_called()


def test_init_storage_bad_filename_raises_oserror(mocker):
    # Patch the open function with our mocked open object
    mock_open = mocker.patch.object(builtins, 'open', side_effect=OSError('Mock OSError'))

    # Call the init_storage function, which should now raise an OSError
    with pytest.raises(OSError):
        init_storage('a/b')

    # Assert that the mocked open function was called with the invalid filename
    mock_open.assert_called_with('a/b', 'w')


def test_init_storage_stores_good_json_file(mocker):
    # Set up the mocked open function
    mock_file_data = []

    def mock_open_side_effect(file, mode='r', *args, **kwargs):
        nonlocal mock_file_data
        mock_file = mocker.mock_open(read_data=''.join(mock_file_data)).return_value
        mock_file.write.side_effect = lambda data: mock_file_data.append(data)
        return mock_file

    mocker.patch('builtins.open', side_effect=mock_open_side_effect)

    # Call the init_storage function with a dummy filename
    dummy_filename = 'dummy.json'
    freezer = freeze_time('2020-03-26 14:13:00')
    freezer.start()
    init_storage(dummy_filename)
    freezer.stop()

    # Assert that the open function was called with the correct arguments
    # (no need to assert this, as we are mocking the open function directly)

    # Assert that the correct data was written to the file
    expected_data = {'time': '2020-03-26 14:13:00', 'level': 0}
    assert json.loads(''.join(mock_file_data)) == expected_data


def test_delete_old_logfile_success(mocker):
    # Arrange
    filename = 'bogus.log'
    mock_os_remove = mocker.patch('os.remove')

    # Act
    result = delete_old_logfile(filename)

    # Assert
    mock_os_remove.assert_called_once_with(filename)
    assert result == True


def test_delete_old_logfile_failure(mocker):
    # Arrange
    filename = 'nonexistent.log'
    mock_os_remove = mocker.patch('os.remove', side_effect=OSError)

    # Act
    result = delete_old_logfile(filename)

    # Assert
    mock_os_remove.assert_called_once_with(filename)
    assert result == False


def arg_helper(*L):
    assert len(L) in [2, 3]
    a, b, c = L
    assert isinstance(a, int)
    assert isinstance(b, int)
    assert isinstance(c, str)


def test_create_files_first_run(mock_file_system):
    # Arrange
    log_filename = 'test.log'
    json_filename = 'test.json'
    json_future_filename = 'test_future.json'

    mock_path, mock_delete_old_logfile, mock_init_logfile, mock_init_future, mock_init_storage = mock_file_system
    mock_path.return_value.is_file.side_effect = [False, False]

    # Act
    first_run = create_files(log_filename, json_filename, json_future_filename)

    # Assert
    assert first_run == True
    mock_init_storage.assert_called_once_with(json_filename)
    mock_delete_old_logfile.assert_called_once_with(log_filename)
    mock_init_logfile.assert_called_once_with(log_filename)
    mock_init_future.assert_called_once_with(json_future_filename)


def test_create_files_subsequent_run(mock_file_system, mocker):
    # Arrange
    log_filename = 'test.log'
    json_filename = 'test.json'
    json_future_filename = 'test_future.json'

    mock_path, mock_delete_old_logfile, mock_init_logfile, mock_init_future, mock_init_storage = mock_file_system
    mock_path.return_value.is_file.side_effect = [True, True]
    mocker.patch('os.path.getsize', return_value=1)  # Mock file size greater than 0

    # Act
    first_run = create_files(log_filename, json_filename, json_future_filename)

    # Assert
    assert first_run == False
    mock_init_storage.assert_not_called()
    mock_delete_old_logfile.assert_not_called()
    mock_init_logfile.assert_not_called()
    mock_init_future.assert_not_called()


def test_init_future(mocker):
    # Arrange
    mock_open = mocker.patch('builtins.open', mocker.mock_open())

    # Define the expected JSON data to be written
    expected_data = []

    # Act
    init_future('test_future.json')

    # Assert
    mock_open.assert_called_once_with('test_future.json', 'w')
    mock_open().write.assert_called_once_with(json.dumps(expected_data))


def test_init_logfile(mocker):
    # Arrange
    mock_open = mocker.patch('builtins.open', mocker.mock_open())
    mock_print = mocker.patch('builtins.print')

    log_filename = 'test.log'

    # Act
    init_logfile(log_filename)

    # Assert
    mock_open.assert_called_once_with(log_filename, 'a+')
    mock_print.assert_called_once_with("Start of log file", file=mock_open.return_value)
