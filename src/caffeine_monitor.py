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

from src.utils import check_which_environment, parse_args


class CaffeineMonitor:
    half_life = 360  # in minutes

    def __init__(self, iofile, ags):
        """
        :param iofile: a .json file handle, open for r+, to store and
               read a time and caffeine level
        :param ags: an argparse.Namespace object with .mg as the amount
                    of caffeine consumed and .mins as how long ago the
                    caffeine was consumed
        """
        self.iofile = iofile
        self.data_dict = {}
        self.mg_to_add = int(ags.mg)
        self.mins_ago = int(ags.mins)

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

    def write_file(self):
        self.iofile.seek(0)
        self.iofile.truncate(0)
        log_mesg = (f'level is {round(self.data_dict["level"], 1)} '
                    f'at {self.data_dict["time"]}')
        if self.mg_to_add:
            log_mesg = f'{self.mg_to_add} mg added: ' + log_mesg
            logging.info(log_mesg)
        else:
            logging.debug(log_mesg)
        json.dump(self.data_dict, self.iofile)

    def decay_prev_level(self):
        """
        Reduce stored level to account for decay since that value
        was written
        """
        curr_time = datetime.today()
        stored_time = datetime.strptime(self.data_dict['time'],
                                        '%Y-%m-%d_%H:%M')
        minutes_elapsed = (curr_time -
                           stored_time) / timedelta(minutes=1)
        self.data_dict['time'] = datetime.strftime(curr_time,
                                                   '%Y-%m-%d_%H:%M')
        self.data_dict['level'] *= pow(0.5, (minutes_elapsed /
                                             self.half_life))

    def decay_before_add(self):
        """
        Decay caffeine consumed some time ago (or in the future)
        before it gets added to current level.

        :return: None
        Called by: main()
        """
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
    try:
        outfile = open(fname, 'w')
    except OSError as er:
        print('Unable to create .json file in `init_storage()`', er)
        raise
    time_now = datetime.strftime(datetime.today(), '%Y-%m-%d_%H:%M')
    start_level = 0
    json.dump({"time": time_now, "level": start_level}, outfile)
    outfile.close()


def delete_old_logfile(fname):
    try:
        os.remove(fname)
        return True
    except OSError:
        return False


if __name__ == '__main__':
    if len(sys.argv) > 4:
        print('Usage: program_name [mgs of caffeine to add] '
              '[minutes ago caffeine was added] [-t | --test flag]')
        sys.exit(0)

    current_environment = check_which_environment()
    args = parse_args(sys.argv[1:])
    config = read_config_file('src/caffeine.ini')

    check_cla_match_env(current_environment, args)
    logging.basicConfig(filename=config[current_environment]['log_file'],
                        level=logging.INFO,
                        format='%(message)s')

    json_filename = config[current_environment]['json_file']
    log_filename = config[current_environment]['log_file']
    my_file = Path(json_filename)
    if not my_file.is_file():
        init_storage(json_filename)
        delete_old_logfile(log_filename)  # if it exists
    try:
        file = open(json_filename, 'r+')
    except OSError as e:
        print('Unable to open .json file', e)
        raise
    else:
        with file:
            monitor = CaffeineMonitor(file, args)
            monitor.main()
