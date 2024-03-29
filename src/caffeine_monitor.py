#!/usr/bin/env python3.9

# file: src/caffeine_monitor.py
# 2019-10-08


"""
Give a rough estimate of the quantity of caffeine
in the user's body, in mg
"""
from datetime import datetime, timedelta
import json
import logging

from src.utils import set_up


COFFEE_MINS_DECREMENT = 15
SODA_MINS_DECREMENT = 20


class CaffeineMonitor:
    half_life = 360  # in minutes

    def __init__(self, logfile, iofile, iofile_future, first_run, ags):
        """
        # :param logfile: an opened file handle
        # :param iofile: an opened file handle
        # :param iofile_future: an opened file handle
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
        self._curr_time = datetime.today()
        self.log_contents = ()

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
        first_line = ''
        last_line = ''
        num_lines = 0
        for log_line in self.logfile:
            num_lines += 1
            if not first_line:
                first_line = log_line.strip()
            last_line = log_line.strip()

        if 0 <= num_lines < 2:
            last_line = ''

        self.log_contents = (first_line, last_line, num_lines)

    def read_file(self):
        """Read initial time and caffeine level from file"""
        self.data_dict = json.load(self.iofile)
        if not self.data_dict:
            self.data_dict = {'time': datetime.now(), 'level': 0.0}

    def read_future_file(self):
        """Read future changes from file"""
        # the sort is redundant; items are sorted before write to file
        self.future_list = sorted(json.load(self.iofile_future), key=lambda x: x['time'], reverse=True)
    
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
        stored_time = datetime.strptime(self.data_dict['time'],
                                        '%Y-%m-%d_%H:%M')
        minutes_elapsed = (self.curr_time -
                           stored_time) / timedelta(minutes=1)
        self.data_dict['time'] = datetime.strftime(self.curr_time,
                                                   '%Y-%m-%d_%H:%M')
        self.data_dict['level'] *= pow(0.5, (minutes_elapsed /
                                             self.half_life))

    def decay_before_add(self, amt_to_decay=None):
        """
        Decay caffeine consumed some time ago
        before it gets added to current level.

        :return: net change rounded to 1 digit past decimal point
        Called by: process_item()
        """
        if amt_to_decay is None:
            amt_to_decay = self.mg_to_add

        # calculate the time at which caffeine was consumed
        old_time = self.curr_time - timedelta(minutes=self.mins_ago)
        minutes_elapsed = (self.curr_time - old_time) / timedelta(minutes=1)
        net_change = (amt_to_decay *
                      pow(0.5, (minutes_elapsed / self.half_life)))
        self.mg_net_change = round(net_change, 1)

    def add_caffeine(self):
        """
        Called by: self.add_coffee()
        """
        if not self.mg_net_change:
            return
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
            self.mins_ago -= COFFEE_MINS_DECREMENT

    def add_soda(self):
        """
        Called by: main()
        """
        # drink 65% now, 25% after SODA_MINS_DECREMENT minutes,
        # remaining 10% after another SODA_MINS_DECREMENT minutes
        soda_amt = self.mg_to_add

        first_amt = soda_amt * 0.65
        self.mg_net_change = first_amt
        # self.mins_ago = 0
        self.process_item()

        second_amt = soda_amt * 0.25
        self.mins_ago -= SODA_MINS_DECREMENT
        self.mg_net_change = second_amt
        self.process_item()

        third_amt = soda_amt * 0.1
        self.mins_ago -= SODA_MINS_DECREMENT
        self.mg_net_change = third_amt
        self.process_item()

    def process_future_list(self):
        """
        Process each item from self.future_list

        Called by: main()
        """
        self.future_list.sort(key=lambda x: x['time'], reverse=True)
        while self.future_list:
            item = self.future_list.pop()
            item_time = datetime.strptime(item['time'], '%Y-%m-%d_%H:%M')
            self.mins_ago = (self.curr_time - item_time) / timedelta(minutes=1)
            self.mg_net_change = item['level']
            self.process_item()
        self.new_future_list.sort(key=lambda x: x['time'], reverse=True)

    def process_item(self):
        """
        Process one caffeine item

        Called by: self.add_coffee(), self.add_soda(), 
                   self.process_future_list()
        """
        if self.mg_net_change == 0:
            return

        if self.mins_ago < 0:  # item is still in the future
            time = (datetime.strptime(self.data_dict['time'], '%Y-%m-%d_%H:%M') +
                    timedelta(minutes=-self.mins_ago))
            new_item = {"time": time.strftime('%Y-%m-%d_%H:%M'), "level": self.mg_net_change}

            # Find the correct position to insert the new item based on its time
            insert_index = 0
            for i, item in enumerate(self.new_future_list):
                if time > datetime.strptime(item['time'], '%Y-%m-%d_%H:%M'):
                    insert_index = i + 1

            # Insert the new item at the correct position
            self.new_future_list.insert(insert_index, new_item)
        elif self.mins_ago == 0:
            self.add_caffeine()
        else:
            self.decay_before_add(self.mg_net_change)
            self.add_caffeine()
            
    def update_time(self):
        """
        Called by: main()
        """
        self.data_dict['time'] = datetime.strftime(datetime.today(),
                                                   '%Y-%m-%d_%H:%M')

    @property
    def curr_time(self):
        return self._curr_time

    @curr_time.setter
    def curr_time(self, new_time):
        self._curr_time = new_time

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
