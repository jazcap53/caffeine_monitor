from argparse import Namespace
import os
import pytest
import sys
import datetime
import logging

from src.caffeine_monitor import (CaffeineMonitor, check_which_environment,
                                  read_config_file, check_cla_match_env,
                                  parse_clas)


def test_can_make_caffeine_monitor_instance(get_test_files):
    nmspc = Namespace(mg=100, mins=180)
    cm = CaffeineMonitor(get_test_files[1], nmspc)
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


def test_read_file(get_test_files):
    with open(get_test_files[1], 'r+') as j_file_handle:
        cm = CaffeineMonitor(j_file_handle, Namespace(mg=200, mins=360,
                                                      test=True))
        assert(isinstance(cm, CaffeineMonitor))
        cm.read_file()
        assert cm.data_dict['level'] == 48
        assert cm.data_dict['time'] == datetime.datetime(2020, 4, 1, 12, 51)


def test_write_file(get_test_files, mocker, caplog):
    with open(get_test_files[1], 'r+') as j_file_handle, \
         open(get_test_files[0], 'r+') as l_file_handle:
        cm = CaffeineMonitor(j_file_handle, Namespace(mg=140, mins=0,
                                                      test=True))
        assert(isinstance(cm, CaffeineMonitor))
        # mocker.patch('logging.basicConfig')
        # logging.basicConfig(stream=sys.stdout,
        #                     level=logging.DEBUG,
        #                     format='%(message)s')
        # mocker.patch.dict('CaffeineMonitor.data_dict', {'level': 140, 'time': 0})
        cm.data_dict = {'level': 140, 'time': 0}
        caplog.set_level('DEBUG', logger=str(get_test_files[0]))
        cm.write_file()

        # out = capsys.readouterr()[0]
        assert cm.mg_to_add == 140
        assert cm.mins_ago == 0
        # assert out == '140 mg added: level is 140.0 at time 06:25'
        assert len(caplog.records) == 1