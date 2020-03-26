#!/usr/bin/env python3.7

# file: caffeine_monitor.py
# andrew jarcho
# 2019-10-08


"""
Give a rough estimate of the quantity of caffeine
in the user's body, in mg
"""
from datetime import datetime, timedelta
import sys
import os
import json
from pathlib import Path
import logging
import configparser
import argparse


def check_which_environment():
    try:
        which_environment = os.environ['CAFF_ENV']
        if which_environment not in ('prod', 'test'):
            raise KeyError
    except KeyError:
        print('Please define environment variable CAFF_ENV as prod or test')
        raise
    return which_environment


def read_config_file(config_file):
    conf = configparser.ConfigParser()
    # config.read('caffeine.ini')
    conf.read(config_file)
    return conf


def parse_clas():
    parser = argparse.ArgumentParser()
    parser.add_argument('-t', '--test', action='store_true',
                        help='Use test environment')
    parser.add_argument('mg', nargs='?', type=int, default=0,
                        help='mg of caffeine to add (may be negative)')
    parser.add_argument('mins', nargs='?', type=int, default=0,
                        help='minutes ago caffeine was added (may be negative)')
    return parser.parse_args()


current_environment = check_which_environment()
config = read_config_file('caffeine.ini')
args = parse_clas()

logging.basicConfig(filename=config[current_environment]['log_file'],
                    level=logging.INFO,
                    format='%(message)s')


def check_env_match(cur_env):
    if 'test' in sys.argv[0]:
        args.test = True

    if args.test and cur_env == 'prod':
        print("Please switch to the test environment with 'export CAFF_ENV=test'")
        sys.exit(0)

    if not args.test and cur_env == 'test':
        print("You may switch to the production environment with 'export CAFF_ENV=prod'")
        sys.exit(0)


check_env_match(current_environment)


class CaffeineMonitor:
    half_life = 360  # in minutes

    def __init__(self, iofile, mg=args.mg, mins_ago=args.mins):
        """
        :param iofile: a .json file handle, open for r+, to store and
               read a time and caffeine level
        :param mg: the amount of caffeine consumed by user
        :param mins_ago: how long ago the caffeine was consumed
        """
        self.iofile = iofile
        self.data_dict = {}
        self.mg_to_add = mg
        self.mins_ago = mins_ago

    def main(self):
        """Driver"""
        self.read_file()
        self.decay_prev_level()
        if self.mins_ago:
            self.decay_before_add()
        if self.mg_to_add:
            self.add_caffeine()
        self.update_time()
        self.write_file()
        print(self)

    def read_file(self):
        """Read initial time and caffeine level from file"""
        self.data_dict = json.load(self.iofile)
        self.data_dict['time'] = datetime.strptime(self.data_dict['time'],
                                                   '%Y-%m-%d_%H:%M')

    def write_file(self):
        self.iofile.seek(0)
        self.iofile.truncate(0)
        log_mesg = f'level is {round(self.data_dict["level"], 1)} at {self.data_dict["time"]}'
        if self.mg_to_add:
            log_mesg = f'{self.mg_to_add} mg added: ' + log_mesg
            logging.info(log_mesg)
        else:
            logging.debug(log_mesg)
        json.dump(self.data_dict, self.iofile)

    def decay_prev_level(self):
        """
        Reduce stored level to account for decay since value was last read
        """
        curr_time = datetime.today()
        minutes_elapsed = (curr_time -
                           self.data_dict['time']) / timedelta(minutes=1)
        self.data_dict['time'] = datetime.strftime(curr_time,
                                                   '%Y-%m-%d_%H:%M')
        self.data_dict['level'] *= pow(0.5, (minutes_elapsed / self.half_life))

    def decay_before_add(self):
        curr_time = datetime.today()
        old_time = curr_time - timedelta(minutes=self.mins_ago)
        minutes_elapsed = (curr_time - old_time) / timedelta(minutes=1)
        self.mg_to_add *= pow(0.5, (minutes_elapsed / self.half_life))
        self.mg_to_add = round(self.mg_to_add, 1)

    def add_caffeine(self):
        self.data_dict['level'] += self.mg_to_add

    def update_time(self):
        self.data_dict['time'] = datetime.strftime(datetime.today(),
                                                   '%Y-%m-%d_%H:%M')

    def __str__(self):
        return (f'Caffeine level is {round(self.data_dict["level"], 1)} '
                f'mg at time {self.data_dict["time"]}')


def init_storage(fname):
    """Create a .json file with initial values for time and level"""
    outfile = open(fname, 'w')
    time_now = datetime.strftime(datetime.today(), '%Y-%m-%d_%H:%M')
    start_level = 0
    json.dump({"time": time_now, "level": start_level}, outfile)
    outfile.close()


if __name__ == '__main__':
    if len(sys.argv) > 4:
        print('Usage: program_name <mgs of caffeine to add> '
              '<minutes ago caffeine was added>')
        sys.exit(0)

    filename = config[current_environment]['json_file']
    my_file = Path(filename)
    if not my_file.is_file():
        init_storage(filename)  # TODO: delete old .log file if any
    with open(filename, 'r+') as storage:
        monitor = CaffeineMonitor(storage,
                                  int(args.mg),
                                  int(args.mins))
        monitor.main()
