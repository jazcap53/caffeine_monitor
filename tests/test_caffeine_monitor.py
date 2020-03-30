from argparse import Namespace
import os
import pytest
import sys
from datetime import datetime


from freezegun import freeze_time

from src.caffeine_monitor import (CaffeineMonitor, check_which_environment,
                                  read_config_file, check_cla_match_env,
                                  parse_clas)


def test_can_make_caffeine_monitor_instance(test_files):
    nmspc = Namespace(mg=100, mins=180)
    cm = CaffeineMonitor(test_files[1], nmspc)
    assert isinstance(cm, CaffeineMonitor)
    assert cm.mg_to_add == 100
    assert cm.mins_ago == 180


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


def test_read_file(test_files):
    with open(test_files[1], 'r+') as j_file_handle:
        cm = CaffeineMonitor(j_file_handle, Namespace(mg=200, mins=360,
                                                      test=True))
        assert(isinstance(cm, CaffeineMonitor))
        cm.read_file()
        assert cm.data_dict['level'] == 48
        dt_out = datetime(2020, 4, 1, 12, 51)
        assert cm.data_dict['time'] == datetime.strftime(dt_out,
                                                         '%Y-%m-%d_%H:%M')


def test_write_file_add_mg(cm, test_files, caplog):
    with open(test_files[0], 'r+') as l_file_handle:
        cur_time = datetime.now().strftime('%Y-%m-%d_%H:%M')
        cm.data_dict = {'level': 140.0, 'time': cur_time}
        caplog.set_level('INFO')

        cm.mg_to_add = 140

        cm.write_file()

        assert f'140 mg added: level is 140.0 at {cur_time}' in caplog.text
        assert len(caplog.records) == 1


def test_write_file_add_no_mg(cm, test_files, caplog):
    with open(test_files[0], 'r+') as l_file_handle:
        cur_time = datetime.now().strftime('%Y-%m-%d_%H:%M')
        cm.data_dict = {'level': 140.0, 'time': cur_time}
        caplog.set_level('DEBUG')

        cm.write_file()

        assert f'level is 140.0 at {cur_time}' in caplog.text
        assert len(caplog.records) == 1


# def test_decay_prev_level(cm, mocker):
#     cm.read_file()  # loads cm.data_dict from file
#     assert cm.data_dict['level'] == 48.0
#     assert cm.data_dict['time'] == datetime.datetime(2020, 4, 1, 12, 51)
#     freezer = freeze_time('2020-04-01 18:51')
#     freezer.start()
#     cm.decay_prev_level()
#     freezer.stop()
#     assert cm.data_dict['level'] == 24.0  # level decays by 50% in 6 hours
#     assert cm.data_dict['time'] == datetime.datetime(2020, 4, 1, 18, 51)