# file: utils.py
# created: 2020-04-05
import os
import sys
import argparse
import configparser
from datetime import datetime
import json
from pathlib import Path
import logging

CONFIG_FILENAME = 'src/caffeine.ini'


def check_which_environment():
    """
    :return: the current environment ('prod', 'test', or 'pytesting')
    """
    which_env = os.environ.get('CAFF_ENV')
    if which_env is None or which_env not in ('prod', 'test', 'pytesting'):
        print('\nPlease export environment variable CAFF_ENV as '
              'prod, test, or pytesting\n')
        sys.exit(0)
    return which_env


def parse_args(args=None):
    """
    Parse the command line arguments
    :return: an argparse.Namespace instance
    """
    if args is None:
        args = sys.argv[1:]

    # Check for multiple instances of -b/--bev argument
    if args.count('--bev') + args.count('-b') > 1:
        raise ValueError("Duplicate -b/--bev argument")

    parser = argparse.ArgumentParser(description='Estimate the quantity of caffeine (in mg) in the user\'s body')

    env_group = parser.add_mutually_exclusive_group()
    env_group.add_argument('-t', '--test', action='store_true', help='Use test environment')
    env_group.add_argument('-q', '--pytesting', dest='pytesting', action='store_true', help='Use pytesting environment for pytest runs')

    parser.add_argument('mg', nargs='?', type=int, default=0, help='amount of caffeine added (may be 0)')
    parser.add_argument('mins', nargs='?', type=int, default=0, help='minutes ago caffeine was added (may be negative, 0, or omitted)')

    # Parse -b/--bev separately with a default value
    bev_parser = parser.add_argument_group('beverage options')
    bev_parser.add_argument('-b', '--bev', choices=['coffee', 'soda', 'chocolate'], default='coffee', help="beverage: 'coffee' (default), 'soda', or 'chocolate'")

    if '-h' in args or '--help' in args:
        parser.print_help()
        sys.exit(0)

    args = parser.parse_args(args)

    if args.mins < 0:
        print("minutes ago argument (mins) must not be < 0")
        sys.exit(1)

    return args


def create_files(log_filename, json_filename, json_future_filename):
    first_run = False

    my_file = Path(json_filename)
    my_file_future = Path(json_future_filename)
    my_logfile = Path(log_filename)  # TODO: obsolete ???

    if not my_file.is_file() or os.path.getsize(my_file) == 0:
        first_run = True
        init_storage(json_filename)
        delete_old_logfile(log_filename)  # if it exists
        init_logfile(log_filename)
        if not my_file_future.is_file():
            init_future(json_future_filename)
    else:
        pass

    return first_run


def read_config_file(config_file):
    conf = configparser.ConfigParser()
    conf.read(config_file)
    return conf


def check_cla_match_env(cur_env, ags):
    """
    Exit with message if the current environment does not match
    the given command line arguments.
    :param cur_env: the current environment ('test', 'prod', or 'pytesting')
    :param ags: an argparse.Namespace object
    :return: None
    """
    ags.test = True if '-t' in sys.argv or '--test' in sys.argv else False
    ags.pytesting = True if '-q' in sys.argv or '--pytesting' in sys.argv else False  # Check for -q or --pytesting flag

    if ags.pytesting:
        if cur_env != 'pytesting':
            print("pytest run detected, but environment is not set to 'pytesting'.")
            print("Please switch to the pytesting environment with 'export CAFF_ENV=pytesting'")
            sys.exit(0)
    elif ags.test:
        if cur_env == 'prod':
            print("Please switch to the test environment with 'export CAFF_ENV=test'")
            sys.exit(0)
        elif cur_env == 'pytesting':
            print("You are in the pytesting environment, which is intended for pytest runs only.")
            print("Please switch to the test environment with 'export CAFF_ENV=test'")
            sys.exit(0)
    else:  # not ags.test and not ags.q
        if cur_env == 'test':
            print("You may switch to the production environment with 'export CAFF_ENV=prod'")
            sys.exit(0)
        elif cur_env == 'pytesting':
            print("You are in the pytesting environment, which is intended for pytest runs only.")
            print("Please switch to the production environment with 'export CAFF_ENV=prod'")
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
            json.dump([], outfile_future)
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


def init_logfile(fname):
    """
    Called by: set_up()
    """
    try:
        with open(fname, 'a+') as logfile:
            print("Start of log file", file=logfile)
    except OSError as er:
        print('Unable to create log file in `init_logfile()`', er)
        raise


def set_up():
    current_environment = None
    try:
        current_environment = check_which_environment()
    except ValueError as e:
        print(e)
        sys.exit(0)

    args = parse_args(sys.argv[1:])
    config = read_config_file(CONFIG_FILENAME)

    check_cla_match_env(current_environment, args)
    json_filename = config[current_environment]['json_file']
    json_future_filename = config[current_environment]['json_file_future']
    log_filename = config[current_environment]['log_file']

    first_run = create_files(log_filename, json_filename, json_future_filename)

    logging.basicConfig(filename=config[current_environment]['log_file'],
                        level=logging.INFO,
                        format='%(levelname)s: %(message)s')
    return log_filename, json_filename, json_future_filename, first_run, args

