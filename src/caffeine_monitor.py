#!/usr/bin/env python3.9

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

    def __init__(self, iofile, iofile_future, ags):
        """
        :param iofile: a .json file handle, open for r+, to store and
               read a time and caffeine level
        :param iofile_future: a .json file handle, open for r+, to 
               store and read future time and level changes.
               May be empty.
        :param ags: an argparse.Namespace object with .mg as the amount
                    of caffeine consumed and .mins as how long ago the
                    caffeine was consumed
        """
        self.iofile = iofile
        self.iofile_future = iofile_future
        self.data_dict = {}  # data to be read from and dumped to .json file
        self.mg_to_add = int(ags.mg)
        self.mins_ago = int(ags.mins)
        self.mg_net_change = 0.0
        self.beverage = ags.bev
        self.future_list = []

    def main(self):
        """Driver"""
        self.read_file()  # sets self.data_dict
        self.read_future_file()  # sets self.future_list
        self.decay_prev_level()
        if self.mins_ago:
            self.mg_net_change = self.decay_before_add()
        else:
            self.mg_net_change = self.mg_to_add
        if self.mg_to_add:
            self.add_caffeine()  # change to self.add_coffee() or self.add_soda()
        self.update_time()
        self.write_file()
        print(self)

    def read_file(self):
        """Read initial time and caffeine level from file"""
        self.data_dict = json.load(self.iofile)
        print(f'type self.data_dict["time"] is {type(self.data_dict["time"])}')
        print(f'type self.data_dict["level"] is {type(self.data_dict["level"])}')

    def read_future_file(self):
        """Read future changes from file"""
        self.data_list = json.load(self.iofile_future)
    
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

    def write_future_file(self):
        self.data_list.sort(key=lambda x: x['time'])
        json.dump(self.future_list, self.iofile_future, indent=4)

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

        :return: net change rounded to 1 digit past decimal point
        Called by: main()
        """
        curr_time = datetime.today()
        old_time = curr_time - timedelta(minutes=self.mins_ago)
        minutes_elapsed = (curr_time - old_time) / timedelta(minutes=1)
        net_change = (self.mg_to_add *
                      pow(0.5, (minutes_elapsed / self.half_life)))
        return round(net_change, 1)

    def add_caffeine(self):
        self.data_dict['level'] += self.mg_net_change

    def add_coffee(self):
        pass  # drink 1/4 of qty at self.mins_ago, then 1/4 of qty every 15 min

    def add_soda(self):
        pass  # drink 65% at self.mins_ago, 25% after 20 min, 10% after 20 min

    def update_time(self):
        self.data_dict['time'] = datetime.strftime(datetime.today(),
                                                   '%Y-%m-%d_%H:%M')

    def __str__(self):
        return (f'Caffeine level is {round(self.data_dict["level"], 1)} '
                f'mg at time {self.data_dict["time"]}')


if __name__ == '__main__':
    json_filename, json_filename_future, args = set_up()

    try:
        file = open(json_filename, 'r+')
    except OSError as e:
        print('Unable to open .json file', e)
        raise
    else:
        with file:
            try:
                file_future = open(json_filename_future, 'r+')
            except OSError as e:
                print('Unable to open future .json file', e)
                raise    
            else:         
                monitor = CaffeineMonitor(file, file_future, args)
                monitor.main()
