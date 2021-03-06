#!/usr/bin/env python3.7

# file: caffeine_monitor.py
# andrew jarcho
# 2019-10-08


"""
Give a rough estimate of the quantity of caffeine
in the user's body, in mg
"""
from datetime import datetime, timedelta
import json
import logging

from src.utils import set_up


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
        self.data_dict = {}  # data to be read from and dumped to .json file
        self.mg_to_add = int(ags.mg)
        self.mins_ago = int(ags.mins)
        self.mg_net_change = 0.0

    def main(self):
        """Driver"""
        self.read_file()
        self.decay_prev_level()
        if self.mins_ago:
            self.mg_net_change = self.decay_before_add()
        else:
            self.mg_net_change = self.mg_to_add
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
        if self.mg_net_change:
            log_mesg = (f'{self.mg_net_change:.1f} mg added ({self.mg_to_add} '
                        f'mg, {self.mins_ago} mins ago): ' + log_mesg)
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
        net_change = (self.mg_to_add *
                      pow(0.5, (minutes_elapsed / self.half_life)))
        return round(net_change, 1)

        # self.mg_net_change = (self.mg_to_add *
        #                       pow(0.5, (minutes_elapsed / self.half_life)))
        # self.mg_net_change = round(self.mg_net_change, 1)

    def add_caffeine(self):
        # self.mg_net_change += self.mg_to_add
        # self.data_dict['level'] += self.mg_to_add
        if not self.mins_ago:
            self.mg_net_change = self.mg_to_add
        self.data_dict['level'] += self.mg_net_change  # if self.mins_ago else self.mg_to_add

    def update_time(self):
        self.data_dict['time'] = datetime.strftime(datetime.today(),
                                                   '%Y-%m-%d_%H:%M')

    def __str__(self):
        return (f'Caffeine level is {round(self.data_dict["level"], 1)} '
                f'mg at time {self.data_dict["time"]}')


if __name__ == '__main__':
    json_filename, args = set_up()

    try:
        file = open(json_filename, 'r+')
    except OSError as e:
        print('Unable to open .json file', e)
        raise
    else:
        with file:
            monitor = CaffeineMonitor(file, args)
            monitor.main()
