# file: pytesting/test_utils.py

from argparse import Namespace
import src.utils
import sys
import os
import json
import pytest
from pytest_mock import mocker
from freezegun import freeze_time

from src.utils import (check_which_environment, parse_args,
                       read_config_file, check_cla_match_env, init_storage,
                       delete_old_logfile, create_files, init_future, init_logfile,
                       set_up)
import subprocess
from src.caffeine_monitor import CaffeineMonitor
import builtins
import logging


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
def test_parse_args(args, expected):
    if expected == SystemExit:
        with pytest.raises(SystemExit):
            parse_args(args)
    else:
        parsed_args = parse_args(args)
        for key, value in expected.items():
            assert getattr(parsed_args, key) == value


@pytest.mark.parametrize("env, expected_output", [
    (None, "Please export environment variable CAFF_ENV as"),
    ("pytesting", "pytesting"),
    ("prod", "prod"),
    ("test", "test"),
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


def test_read_config_file_fake(tmpdir):
    fh = tmpdir.join("config.ini")
    fh.write('''\
[prod]
json_file = src/caffeine_production.json
log_file = src/caffeine_production.log

[test]
json_file = tests/caff_test.json
log_file = tests/caff_test.log
    ''')
    config = read_config_file(fh)
    assert config.sections() == ['prod', 'test']
    assert config['prod'], {'json_file': 'src/caffeine_production.json',
                            'log_file': 'src/caffeine_production.log'}
    assert config['test'], {'json_file': 'tests/caff_test.json',
                            'log_file': 'tests/caff_test.log'}


@pytest.mark.parametrize(
    "cur_env, test_flag, pytesting_flag, expected_exit",
    [
        ("pytesting", False, True, False),
        ("pytesting", True, False, True),
        ("pytesting", False, False, True),
        ("test", False, True, True),
        ("test", True, False, False),
        ("test", False, False, True),
        ("prod", False, True, True),
        ("prod", True, False, True),
        ("prod", False, False, False),
    ],
)
def test_check_cla_match_env(mocker, cur_env, test_flag, pytesting_flag, expected_exit):
    args = mocker.MagicMock()
    args.test = test_flag
    args.pytesting = pytesting_flag

    mocker.patch("sys.argv", ["script.py"])
    if test_flag:
        mocker.patch("sys.argv", ["script.py", "-t"])
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


def test_init_storage_stores_good_json_file(tmpdir):
    filename = tmpdir.join('delete_me.json')
    freezer = freeze_time('2020-03-26 14:13')
    freezer.start()
    init_storage(filename)
    freezer.stop()
    with open(filename) as file_handle:
        line_read = json.load(file_handle)
        assert line_read == {'time': '2020-03-26_14:13', 'level': 0}
        file_handle.close()
    os.remove(filename)


def test_delete_old_logfile_success(tmpdir):
    filename = tmpdir.join('bogus.log')
    with open(filename, 'w') as handle:
        handle.close()
    assert delete_old_logfile(filename)


def test_delete_old_logfile_failure(tmpdir):
    name_string = 'bogus.log'
    filename = tmpdir.join(name_string)
    while os.path.isfile(filename):  # make *sure* file doesn't exist
        name_string += 'x'
        filename = tmpdir.join(name_string)
    assert not delete_old_logfile(filename)


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


@pytest.mark.parametrize('caff_env', ['prod', 'test', 'pytesting', 'nonsense', None, ''])
def test_set_up(mocker, caff_env):
    # Arrange
    mock_args = mocker.MagicMock()
    mock_parse_args = mocker.patch('src.utils.parse_args', return_value=mock_args)

    expected_args = ['script.py']  # Default value for expected_args

    if caff_env in ('prod', 'test', 'pytesting'):
        mocker.patch.dict('os.environ', {'CAFF_ENV': caff_env})
        if caff_env == 'test':
            expected_args = ['script.py', '-t']
        elif caff_env == 'pytesting':
            expected_args = ['script.py', '-q']
        mocker.patch('sys.argv', expected_args)
    else:
        mocker.patch.dict('os.environ', clear=True)

    mock_config = {
        'prod': {'json_file': 'prod.json', 'json_file_future': 'prod_future.json', 'log_file': 'prod.log'},
        'test': {'json_file': 'test.json', 'json_file_future': 'test_future.json', 'log_file': 'test.log'},
        'pytesting': {'json_file': 'pytesting.json', 'json_file_future': 'pytesting_future.json', 'log_file': 'pytesting.log'}
    }
    mock_read_config_file = mocker.patch('src.utils.read_config_file', return_value=mock_config)

    mock_first_run = True
    mock_create_files = mocker.patch('src.utils.create_files', return_value=mock_first_run)

    mock_check_cla_match_env = mocker.patch('src.utils.check_cla_match_env')  # Mock the function

    mock_logging_basicConfig = mocker.patch('logging.basicConfig')  # Mock logging.basicConfig

    # Act and Assert
    if caff_env in ['prod', 'test', 'pytesting']:
        log_filename, json_filename, json_future_filename, first_run, args = set_up()
        expected_log_filename = mock_config[caff_env]['log_file']
        expected_json_filename = mock_config[caff_env]['json_file']
        expected_json_future_filename = mock_config[caff_env]['json_file_future']

        mock_parse_args.assert_called_once_with(expected_args[1:])  # Assert with expected arguments
        mock_read_config_file.assert_called_once_with('src/caffeine.ini')
        mock_check_cla_match_env.assert_called_once_with(caff_env, mock_args)  # Use the mocked function
        mock_create_files.assert_called_once_with(expected_log_filename, expected_json_filename, expected_json_future_filename)
        mock_logging_basicConfig.assert_called_once_with(filename=expected_log_filename, level=logging.INFO,
                                                         format='%(levelname)s: %(message)s')
        assert log_filename == expected_log_filename
        assert json_filename == expected_json_filename
        assert json_future_filename == expected_json_future_filename
        assert first_run == mock_first_run
        assert args == mock_args
    else:
        with pytest.raises(SystemExit):
            set_up()
