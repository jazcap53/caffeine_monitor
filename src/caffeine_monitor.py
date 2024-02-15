#!/usr/bin/env python3.9

# file: caffeine_monitor.py
# 2019-10-08


"""
Give a rough estimate of the quantity of caffeine
in the user's body, in mg
"""
from datetime import datetime, timedelta
import json
import logging

from src.utils import set_up


MINS_DECREMENT = 15  # normally 15


class CaffeineMonitor:
    half_life = 360  # in minutes

    def __init__(self, logfile, iofile, iofile_future, first_run, ags):
        """
        :param logfile: a Path object
        :param iofile: a Path object
        :param iofile_future: a Path object
        :param ags: an argparse.Namespace object with .mg as the amount
                    of caffeine consumed, .mins as how long ago the
                    caffeine was consumed, and .bev as the beverage
        """
        self.logfile = logfile
        self.iofile = iofile
        self.iofile_future = iofile_future
        self.data_dict = {}  # data to be read from and dumped to .json file
        self.mg_to_add = int(ags.mg)
        self.mins_ago = int(ags.mins)
        self.mg_net_change = 0.0
        self.beverage = ags.bev
        self.future_list = []
        self.new_future_list = []
        self.log_line_one = ''
        self.first_run = first_run

    def main(self):
        """Driver"""
        self.read_log()
        self.read_file()  # sets self.data_dict
        self.read_future_file()  # sets self.future_list
        if not self.first_run:
            self.decay_prev_level()

        if self.beverage == "coffee":
            self.add_coffee()
        elif self.beverage == "soda":
            self.add_soda()
        else:
            pass

        self.process_future_list()

        self.update_time()

        self.write_future_file()

        self.write_file()
        print(self)

    def read_log(self):
        pass

    def read_file(self):
        """Read initial time and caffeine level from file"""
        self.data_dict = json.load(self.iofile)
        if not self.data_dict:
            self.data_dict = {'time': datetime.now(), 'level': 0.0}

    def read_future_file(self):
        """Read future changes from file"""
        self.future_list = json.load(self.iofile_future)
    
    def write_file(self):
        self.iofile.seek(0)
        self.iofile.truncate(0)
        json.dump(self.data_dict, self.iofile)

    def write_future_file(self):
        self.iofile_future.seek(0)
        self.iofile_future.truncate()
        self.new_future_list.sort(key=lambda x: x['time'], reverse=True)
        json.dump(self.new_future_list, self.iofile_future, indent=4)

    def write_log(self):
        """
        Called by: self.add_caffeine()
        """
        log_mesg = (f'level is {round(self.data_dict["level"], 1)} '
                    f'at {self.data_dict["time"]}')
        if self.mg_net_change:
            log_mesg = (f'{self.mg_net_change:.1f} mg added ({self.mg_to_add} '
                        f'mg, {self.mins_ago} mins ago): ' + log_mesg)
            logging.info(log_mesg)
        else:
            logging.debug(log_mesg)

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

    def decay_before_add(self, amt_to_decay=None):
        """
        Decay caffeine consumed some time ago
        before it gets added to current level.

        :return: net change rounded to 1 digit past decimal point
        Called by: main()
        """
        if amt_to_decay is None:
            amt_to_decay = self.mg_to_add

        curr_time = datetime.today()
        old_time = curr_time - timedelta(minutes=self.mins_ago)  #TODO: '+' or '-' here
        minutes_elapsed = (curr_time - old_time) / timedelta(minutes=1)
        net_change = (amt_to_decay *
                      pow(0.5, (minutes_elapsed / self.half_life)))
        self.mg_net_change = round(net_change, 1)

    def add_caffeine(self):
        """
        Called by: self.add_coffee()
        """
        self.data_dict['level'] += self.mg_net_change
        self.write_log()        

    def add_coffee(self):
        """
        Called by: main()
        """ 
        quarter = self.mg_to_add / 4
        self.mg_net_change = quarter

        for i in range(4):
            self.process_item()
            self.mins_ago -= MINS_DECREMENT

    def add_soda(self):
        """
        Called by: main()
        """
        pass  # drink 65% at self.mins_ago, 25% after 20 min, 10% after 20 min

    def process_future_list(self):
        """
        Process each item from self.future_list

        Called by: main()
        """
        self.future_list.sort(key=lambda x: x['time'], reverse=True)
        while self.future_list:
            item = self.future_list.pop()
            # self.decay_before_add(item['level'])   # DA suggestion -- doesn't work
            curr_time = datetime.today()
            item_time = datetime.strptime(item['time'], '%Y-%m-%d_%H:%M')
            self.mins_ago = (curr_time - item_time) / timedelta(minutes=1)
            self.mg_net_change = item['level']
            self.process_item()

    def process_item(self):
        """
        Process one caffeine item

        Called by: self.add_coffee(), self.add_soda(), 
                   self.process_future_list()
        """
        amt_to_decay = self.mg_net_change
        if not self.first_run:
            self.decay_before_add(amt_to_decay)
        if self.mg_net_change == 0:
            return

        if self.mins_ago < 0:  # item is still in the future
            time = (datetime.strptime(self.data_dict['time'], '%Y-%m-%d_%H:%M') +
                    timedelta(minutes=-self.mins_ago))
            self.new_future_list.append({"time": time.strftime('%Y-%m-%d_%H:%M'),  
                                         "level": self.mg_net_change})
        elif self.mins_ago == 0:
            self.add_caffeine()
        else:
            self.decay_before_add()
            self.add_caffeine()

    def update_time(self):
        """
        Called by: main()
        """
        self.data_dict['time'] = datetime.strftime(datetime.today(),
                                                   '%Y-%m-%d_%H:%M')

    def __str__(self):
        return (f'Caffeine level is {round(self.data_dict["level"], 1)} '
                f'mg at time {self.data_dict["time"]}')


if __name__ == '__main__':
    log_filename, json_filename, json_filename_future, first_run, args = set_up()

    try:
        logfile = open(log_filename, 'r+')
    except OSError as e:
        print('Unable to open .log file', e)
        raise
    else:
        with logfile:
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
                        monitor = CaffeineMonitor(logfile, file, file_future, first_run, args)
                        monitor.main()
