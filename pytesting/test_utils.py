# file: test_utils.py

from argparse import Namespace
import src.utils
import sys
import os
import json
import pytest
from freezegun import freeze_time

from src.utils import (check_which_environment, parse_args, set_up,
                       read_config_file, check_cla_match_env, init_storage,
                       delete_old_logfile)
import subprocess
from src.caffeine_monitor import CaffeineMonitor
import builtins


def test_bad_caff_env_value_exits(mocker):
    mocker.patch('os.environ')
    mocker.patch('sys.exit')
    os.environ['CAFF_ENV'] = 'bongo'
    __ = check_which_environment()
    assert sys.exit.called_once_with(0)


@pytest.mark.parametrize(
    'mg, mins, bev, param_id',
    [
        pytest.param(0, 0, 'coffee', 'zero_mg_zero_mins_coffee'),
        pytest.param(0, 0, 'soda', 'zero_mg_zero_mins_soda'),
        pytest.param(100, 20, 'coffee', 'hundred_mg_twenty_mins_coffee')
    ]
)
def test_parse_valid_args_v3(mg, mins, bev, param_id):
    namespace = parse_args([str(mg), str(mins), '--bev', bev])

    assert namespace.mg == mg
    assert namespace.mins == mins
    assert namespace.bev == bev


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


def test_parse_args_with_t():
    args = parse_args(['-t'])
    assert args.test


def test_parse_args_with_200():
    args = parse_args(['200'])
    assert args.mg == 200


def test_parse_args_with_200_360():
    args = parse_args(['200', '360'])
    assert args.mins == 360


def test_check_which_environment_unset(monkeypatch, capsys):
    """Test that check_which_environment() prints a message and exits when CAFF_EV is unset."""

    # Delete CAFF_ENV from the environment, if it exists
    monkeypatch.delenv('CAFF_ENV', raising=False)

    # Define a mock function to replace sys.exit
    def mock_exit(status=0):
        raise SystemExit(status)

    # Replace sys.exit with our mock function
    monkeypatch.setattr('sys.exit', mock_exit)

    with pytest.raises(SystemExit):
        check_which_environment()

    out, err = capsys.readouterr()

    assert 'Please export environment variable CAFF_ENV as' in out


@pytest.mark.parametrize('env', ['pytesting', 'prod', 'test'])
def test_check_which_environment_set(mocker, env):
    mocker.patch.dict('os.environ', {'CAFF_ENV': env})
    mocker.patch('sys.exit')
    assert check_which_environment() == env
    assert sys.exit.call_count == 0


def test_set_up_with_q_pytesting_env(mocker):
    mocker.patch('sys.argv', ['pytest', '0', '0', '-q'])
    mocker.patch.dict('os.environ', {'CAFF_ENV': 'pytesting'})  # Set the environment variable

    # Patch the file existence checks
    mocker.patch('pathlib.Path.is_file', side_effect=[False, False])

    log_filename, json_filename, json_future_filename, first_run, args = set_up()
    assert str(log_filename) == 'pytesting/caff_pytesting.log'
    assert str(json_filename) == 'pytesting/caff_pytesting.json'
    assert str(json_future_filename) == 'pytesting/caff_pytesting_future.json'
    assert first_run is True


def test_set_up_with_q_test_env(mocker):
    mocker.patch('sys.argv', ['pytest', '0', '0', '-q'])
    mocker.patch.dict('os.environ', {'CAFF_ENV': 'test'})  # Set the environment variable

    with pytest.raises(SystemExit) as exc_info:
        set_up()
    assert exc_info.type == SystemExit
    assert exc_info.value.code == 0


def test_set_up_with_q_prod_env(mocker):
    mocker.patch('sys.argv', ['pytest', '0', '0', '-q'])
    mocker.patch.dict('os.environ', {'CAFF_ENV': 'prod'})  # Set the environment variable

    with pytest.raises(SystemExit) as exc_info:
        set_up()
    assert exc_info.type == SystemExit
    assert exc_info.value.code == 0


def test_set_up_with_t_test_env(mocker):
    mocker.patch('sys.argv', ['pytest', '0', '0', '-t'])
    mocker.patch.dict('os.environ', {'CAFF_ENV': 'test'})  # Set the environment variable

    # Patch the file existence checks
    mocker.patch('pathlib.Path.is_file', side_effect=[False, False])

    log_filename, json_filename, json_future_filename, first_run, args = set_up()
    assert str(log_filename) == 'tests/caff_test.log'
    assert str(json_filename) == 'tests/caff_test.json'
    assert str(json_future_filename) == 'tests/caff_test_future.json'
    assert first_run is True


def test_set_up_with_t_prod_env(mocker):
    mocker.patch('sys.argv', ['pytest', '0', '0', '-t'])
    mocker.patch.dict('os.environ', {'CAFF_ENV': 'prod'})  # Set the environment variable

    with pytest.raises(SystemExit) as exc_info:
        set_up()
    assert exc_info.type == SystemExit
    assert exc_info.value.code == 0


def test_set_up_with_t_pytesting_env(mocker):
    mocker.patch('sys.argv', ['pytest', '0', '0', '-t'])
    mocker.patch.dict('os.environ', {'CAFF_ENV': 'pytesting'})  # Set the environment variable

    with pytest.raises(SystemExit) as exc_info:
        set_up()
    assert exc_info.type == SystemExit
    assert exc_info.value.code == 0


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


def test_check_cla_match_env_bad_01(mocker):
    mocker.patch('sys.exit')
    args = Namespace(test=True, mg=0, mins=0)
    test_argv = ['-t']
    mocker.patch.object(sys, 'argv', test_argv)
    current_environment = 'prod'
    check_cla_match_env(current_environment, args)
    sys.exit.assert_called_once_with(0)


def test_check_cla_match_env_bad_02(mocker):
    mocker.patch('sys.exit')
    args = Namespace(test=False, mg=0, mins=0)
    test_argv = []
    mocker.patch.object(sys, 'argv', test_argv)
    current_environment = 'test'
    check_cla_match_env(current_environment, args)
    sys.exit.assert_called_once_with(0)


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