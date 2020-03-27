from argparse import Namespace
import os
import pytest
import sys

from src.caffeine_monitor import (CaffeineMonitor, check_which_environment,
                                  read_config_file, check_cla_match_env,
                                  parse_clas)


def test_can_make_caffeine_monitor_instance(c_mon):
    nmspc = Namespace(mg=100, mins=180)
    cm = CaffeineMonitor(c_mon[1], nmspc)
    assert isinstance(cm, CaffeineMonitor)


def test_bad_caff_env_value_exits(mocker):
    mocker.patch('os.environ')
    mocker.patch('sys.exit')
    os.environ['CAFF_ENV'] = 'bongo'
    __ = check_which_environment()
    assert sys.exit.called_once_with(0)


def test_read_config_file():
    config = read_config_file('src/caffeine.ini')
    assert 'prod' in config
    assert 'test' in config
    assert 'json_file' in config['prod']
    assert 'json_file' in config['test']
    assert 'log_file' in config['prod']
    assert 'log_file' in config['test']


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


def test_parse_clas():
    args = parse_clas()
    assert args.mg is not None
    assert args.mins is not None
    assert args.test is not None
    with pytest.raises(AttributeError):
        assert args.bongo is None
