from argparse import Namespace
import os
import pytest
import sys

from caffeine_monitor import (CaffeineMonitor, check_which_environment,
                              read_config_file, check_env_match, parse_clas)


def test_can_make_caffeine_monitor_instance(c_mon):
    nmspc = Namespace(mg=100, mins=180)
    cm = CaffeineMonitor(c_mon[1], nmspc.mg, nmspc.mins)
    assert isinstance(cm, CaffeineMonitor)


def test_bad_caff_env_value_raises(mocker):
    mocker.patch('os.environ')
    os.environ['CAFF_ENV'] = 'bongo'
    with pytest.raises(KeyError):
        __ = check_which_environment()


def test_read_config_file():
    config = read_config_file('caffeine.ini')
    assert 'prod' in config
    assert 'test' in config
    assert 'json_file' in config['prod']
    assert 'json_file' in config['test']
    assert 'log_file' in config['prod']
    assert 'log_file' in config['test']


def test_check_env_match_with_pytest_and_prod(mocker):
    mocker.patch('sys.exit')
    mocker.patch('sys.argv')
    # mocker.patch('test_or_prod')
    sys.argv[0] = 'pytest'
    current_environment = 'prod'
    check_env_match(current_environment)
    sys.exit.assert_called_once_with(0)
    sys.argv[0] = 'caff'
    current_environment = 'test'
    check_env_match(current_environment)
    sys.exit.assert_called_once_with(0)


def test_parse_clas():
    args = parse_clas()
    assert args.mg is not None
    assert args.mins is not None
    assert args.test is not None
    with pytest.raises(AttributeError):
        assert args.bongo is None
