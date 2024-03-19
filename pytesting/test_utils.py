# file: pytesting/test_utils.py

from argparse import Namespace
import src.utils
import sys
import os
import json
import pytest
from freezegun import freeze_time

from src.utils import (check_which_environment, parse_args, set_up,
                       read_config_file, check_cla_match_env, init_storage,
                       delete_old_logfile, create_files, init_future)
import subprocess
from src.caffeine_monitor import CaffeineMonitor
import builtins


def test_bad_caff_env_value_exits(mocker):
    mocker.patch('os.environ')
    mocker.patch('sys.exit')
    os.environ['CAFF_ENV'] = 'bongo'
    __ = check_which_environment()
    assert sys.exit.called_once_with(0)


# TODO: we don't need such elaborate tests to check the behavior of `argparse`
@pytest.mark.parametrize(
    "args, expected",
    [
        (["-t"], {"test": True}),
        (["200"], {"mg": 200}),
        (["200", "360"], {"mg": 200, "mins": 360}),
        (["0", "0", "--bev", "coffee"], {"mg": 0, "mins": 0, "bev": "coffee"}),
        (["0", "0", "--bev", "soda"], {"mg": 0, "mins": 0, "bev": "soda"}),
        (["100", "20", "--bev", "coffee"], {"mg": 100, "mins": 20, "bev": "coffee"}),
    ],
)
def test_parse_args(args, expected):
    parsed_args = parse_args(args)
    for key, value in expected.items():
        assert getattr(parsed_args, key) == value


@pytest.mark.parametrize('ags', [
    (0, 0, 0, 0),
    (0,),
    (100, '0', 'water')
])
def test_parse_invalid_args(files_mocked, ags):
    """
    Call the script from the command line with an invalid argument
    """
    a, b, c = None, None, None
    open_mock, json_load_mock, json_dump_mock = files_mocked

    had_error = False
    try:
        a, b, c = ags
    except ValueError:
        had_error = True
    try:
        arg_helper(ags)
    except AssertionError:
        had_error = True

    if not had_error:
        nmspc = Namespace(mg=a, mins=b, bev=c)
        with pytest.raises(Exception):
            _ = CaffeineMonitor(open_mock, json_load_mock, json_load_mock, True, nmspc)
    else:  # We had an error, so the test should pass
        pass


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
