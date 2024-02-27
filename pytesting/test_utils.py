# file: test_utils.py

from argparse import Namespace
import sys
import os
import json
# from pathlib import PosixPath
import pytest
from freezegun import freeze_time

from caffeine_monitor.src.utils import (check_which_environment, parse_args, set_up,
                                        read_config_file, check_cla_match_env, init_storage,
                                        delete_old_logfile)
import subprocess
from caffeine_monitor.src.caffeine_monitor import CaffeineMonitor


def test_bad_caff_env_value_exits(mocker):
    mocker.patch('os.environ')
    mocker.patch('sys.exit')
    os.environ['CAFF_ENV'] = 'bongo'
    __ = check_which_environment()
    assert sys.exit.called_once_with(0)


def test_parse_valid_args(tmpdir, mocker):
    # Get the path to the temporary directory
    tmp_dir_path = tmpdir.strpath

    # Create the log file path
    log_file_path = os.path.join(tmp_dir_path, 'test.log')

    # Create a temporary JSON file
    json_file = tmpdir.join('test.json')
    json_file.write('{"time": "2023-04-01_12:00", "level": 0.0}')

    # Create a temporary future JSON file
    json_future_file = tmpdir.join('test_future.json')
    json_future_file.write('[]')

    # Mock the set_up() function to return the temporary files
    mocker.patch('caffeine_monitor.src.utils.set_up', return_value=(
        log_file_path, json_file.strpath, json_future_file.strpath, False,
        Namespace(mg=100, mins=0, bev='coffee', test=False, pytesting=True)))

    with open(log_file_path, 'a+') as log_file:
        print(f'tmp_dir_path: {tmp_dir_path}')
        print(f'log_file_path: {log_file_path}')
        monitor = CaffeineMonitor(log_file, open(json_file.strpath, 'r+'),
                                  open(json_future_file.strpath, 'r+'), False,
                                  Namespace(mg=100, mins=0, bev='coffee'))
        monitor.main()
        log_file.seek(0)
        print('before seek() contents of log file are ')
        print(log_file.read())
        log_file.seek(0)
        print('after seek() contents of log file are ')
        print(log_file.read())
        assert log_file.read() == 'INFO: 25.0 mg added (100 mg, 0 mins ago): level is 25.0 at ...'


def test_parse_invalid_args(tmpdir):
    # Call the script from the command line with an invalid argument
    cmd = [sys.executable, 'src/caffeine_monitor.py', '-t', '-1']
    try:
        subprocess.run(cmd, check=True, capture_output=True)
    except subprocess.CalledProcessError as e:
        # Assert that the script exited with a non-zero code and printed the expected error message
        assert e.returncode != 0
        assert b'minutes ago argument (mins) must not be < 0' in e.stderr
    else:
        pytest.fail("Command should have failed with an error message")


def test_parse_args():
    # args = parse_args(sys.argv[1:])
    args = parse_args()
    assert args.mg is not None
    assert args.mins is not None
    assert args.test is not None
    with pytest.raises(AttributeError):
        assert args.bongo is None


def test_parse_args_with_t():
    args = parse_args(['-t'])
    assert args.test


def test_parse_args_with_200():
    args = parse_args(['200'])
    assert args.mg == 200


def test_parse_args_with_200_360():
    args = parse_args(['200', '360'])
    assert args.mins == 360


def test_check_which_environment_unset(mocker):
    mocker.patch('sys.exit')
    mocker.patch.dict('os.environ', {})
    check_which_environment()
    assert sys.exit.called_once_with(0)


def test_check_which_environment_set_pytesting(mocker):
    mocker.patch.dict('os.environ', {'CAFF_ENV': 'pytesting'})
    assert check_which_environment() == 'pytesting'


def test_check_which_environment_set_test(mocker):
    mocker.patch.dict('os.environ', {'CAFF_ENV': 'prod'})
    assert check_which_environment() == 'prod'


def test_check_which_environment_set_prod(mocker):
    mocker.patch.dict('os.environ', {'CAFF_ENV': 'test'})
    assert check_which_environment() == 'test'


def test_set_up_with_q(mocker):
    mocker.patch('sys.argv')
    sys.argv = ['pytest', '0', '0', '-q']
    log_filename, json_filename, json_future_filename, first_run, args = set_up()
    assert str(log_filename) == 'pytesting/caff_pytesting.log'
    assert str(json_filename) == 'pytesting/caff_pytesting.json'
    assert str(json_future_filename) == 'pytesting/caff_pytesting_future.json'
    assert first_run is False
    assert args == Namespace(mg=0, mins=0, test=False, pytesting=True, bev='coffee')


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


def test_init_storage_bad_filename_raises_oserror():
    with pytest.raises(OSError):
        init_storage('a/b')


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
