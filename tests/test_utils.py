import sys
import os
import json
from argparse import Namespace

import pytest
from freezegun import freeze_time

from src.utils import (check_which_environment, parse_args, set_up,
                       read_config_file, check_cla_match_env, init_storage,
                       delete_old_logfile)


def test_bad_caff_env_value_exits(mocker):
    mocker.patch('os.environ')
    mocker.patch('sys.exit')
    os.environ['CAFF_ENV'] = 'bongo'
    __ = check_which_environment()
    assert sys.exit.called_once_with(0)


def test_parse_args():
    args = parse_args(sys.argv[1:])
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


def test_check_which_environment_set_test(mocker):
    mocker.patch.dict('os.environ', {'CAFF_ENV': 'prod'})
    assert check_which_environment() == 'prod'


def test_check_which_environment_set_prod(mocker):
    mocker.patch.dict('os.environ', {'CAFF_ENV': 'test'})
    assert check_which_environment() == 'test'


def test_set_up(mocker):
    mocker.patch('sys.argv')
    sys.argv = ['pytest', '0', '0', '-t']
    json_filename, args = set_up()
    assert json_filename == 'tests/caff_test.json'
    assert args == Namespace(mg=0, mins=0, test=True)


def test_read_config_file_real():
    config = read_config_file('src/caffeine.ini')
    assert 'prod' in config
    assert 'test' in config
    assert 'json_file' in config['prod']
    assert 'json_file' in config['test']
    assert 'log_file' in config['prod']
    assert 'log_file' in config['test']


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