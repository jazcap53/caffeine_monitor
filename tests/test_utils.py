import sys
import os
from src.utils import check_which_environment, parse_args, set_up
from argparse import Namespace

import pytest


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
