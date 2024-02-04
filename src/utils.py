# file: utils.py
# andrew jarcho
# created: 2020-04-05


import os
import sys
import argparse
import configparser
from datetime import datetime, MAXYEAR
import json
from pathlib import Path
import logging

CONFIG_FILENAME = 'src/caffeine.ini'


def check_which_environment():
    """
    :return: the current environment ('prod' or 'test')
    """
    which_env = os.environ.get('CAFF_ENV')
    if which_env is None or which_env not in ('prod', 'test'):
        print('\nPlease export environment variable CAFF_ENV as '
              'prod or test\n')
        sys.exit(0)
    return which_env


def parse_args(args):
    """
    Parse the command line arguments
    :return: an argparse.Namespace instance
    """
    parser = argparse.ArgumentParser(description='Estimate the quantity '
                                                 'of caffeine (in mg) in the '
                                                 'user\'s body')
    parser.add_argument('-t', '--test', action='store_true',
                        help='Use test environment')
    parser.add_argument('mg', nargs='?', type=int, default=0,
                        help='amount of caffeine added (may be 0)')
    parser.add_argument('mins', nargs='?', type=int, default=0,
                        help='minutes ago caffeine was added '
                             '(may be negative, 0, or '
                             'omitted)')
    parser.add_argument('-b', '--bev', 
                        required=False, 
                        choices=['coffee', 'soda'], 
                        type=str,
                        default='coffee', 
                        help="beverage: 'coffee' (default)"
                        " or soda so far")
    return parser.parse_args(args)


def read_config_file(config_file):
    conf = configparser.ConfigParser()
    conf.read(config_file)
    return conf


def check_cla_match_env(cur_env, ags):
    """
    Exit with message if the current environment does not match
    the given command line arguments.
    :param cur_env: the current environment ('test' or 'prod')
    :param ags: an argparse.Namespace object
    :return: None
    """
    ags.test = True if '-t' in sys.argv or '--test' in sys.argv else False

    if ags.test and cur_env == 'prod':
        print("Please switch to the test environment with "
              "'export CAFF_ENV=test'")
        sys.exit(0)

    if not ags.test and cur_env == 'test':
        print("You may switch to the production environment with "
              "'export CAFF_ENV=prod'")
        sys.exit(0)


def init_storage(fname):
    """Create a .json file with initial values for time and level"""
    time_now = datetime.strftime(datetime.today(), '%Y-%m-%d_%H:%M')
    start_level = 0
    try:
        with open(fname, 'w') as outfile:
            json.dump({"time": time_now, "level": start_level}, outfile)
    except OSError as er:
        print('Unable to create .json file in `init_storage()`', er)
        raise


def init_future(fname):
    """Create an empty .json file"""
    try:
        with open(fname, 'w') as outfile_future:
             json.dump([{"at_time": datetime.strftime(datetime(MAXYEAR, 12, 31), '%Y-%m-%d_%H:%M'), "at_level": 0}], outfile_future)
    except OSError as er:
        print('Unable to create dummy future .json file in `init_future()`',
              er)
        raise


def delete_old_logfile(fname):
    try:
        os.remove(fname)
        return True  # return value only used by testing code at present
    except OSError:
        return False  # ditto


def set_up():
    current_environment = check_which_environment()
    args = parse_args(sys.argv[1:])
    config = read_config_file(CONFIG_FILENAME)

    check_cla_match_env(current_environment, args)
    logging.basicConfig(filename=config[current_environment]['log_file'],
                        level=logging.INFO,
                        format='%(message)s')

    json_filename = config[current_environment]['json_file']
    json_filename_future = config[current_environment]['json_file_future']
    log_filename = config[current_environment]['log_file']
    my_file = Path(json_filename)
    my_file_future = Path(json_filename_future)
    if not my_file.is_file() or os.path.getsize(my_file_future) == 0:
        init_storage(json_filename)
        delete_old_logfile(log_filename)  # if it exists
    if not my_file_future.is_file() or os.path.getsize(my_file_future) == 0:
        init_future(json_filename_future)
    return json_filename, json_filename_future, args
