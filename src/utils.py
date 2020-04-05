# file: utils.py
# andrew jarcho
# created: 2020-04-05


import os
import sys
import argparse
import configparser


def check_which_environment():
    """
    :return: the current environment ('prod' or 'test')
    """
    try:
        which_environment = os.environ['CAFF_ENV']
        if which_environment not in ('prod', 'test'):
            raise KeyError
    except KeyError:
        print('\nPlease export environment variable CAFF_ENV as '
              'prod or test\n')
        sys.exit(0)
    return which_environment


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
                        help='mg of caffeine to add (may be negative, 0, or '
                             'omitted)')
    parser.add_argument('mins', nargs='?', type=int, default=0,
                        help='minutes ago caffeine was added '
                             '(may be negative, 0, or '
                             'omitted)')
    return parser.parse_args(args)


def read_config_file(config_file):
    conf = configparser.ConfigParser()
    conf.read(config_file)
    return conf
