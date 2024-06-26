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
        self.mg_to_add_now = 0.0
        self.mins_ago = int(ags.mins)
        self.time_entered = datetime.now()
        self.when_to_process = self.time_entered - timedelta(minutes=self.mins_ago)
        self.mg_net_change = 0.0
        self.beverage = ags.bev
        self.future_list = []
        self.new_future_list = []
        self.log_line_one = ''
        self.first_run = first_run
        self.current_time = datetime.today()
        self.current_item = None
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
            self.data_dict = {'time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'), 'level': 0.0}

    def read_future_file(self):
        """Read future changes from file"""
        try:
            future_data = json.load(self.iofile_future)
            self.future_list = sorted(
                [
                    {
                        'when_to_process': datetime.strptime(item['when_to_process'], '%Y-%m-%d %H:%M:%S'),
                        'time_entered': datetime.strptime(item['time_entered'], '%Y-%m-%d %H:%M:%S'),
                        'level': item['level']
                    }
                    for item in future_data
                ],
                key=lambda x: x['when_to_process'],
                reverse=True
            )
        except json.JSONDecodeError as e:
            print(f"Error decoding JSON data in {self.iofile_future.name}: {e}")
            self.future_list = []  # Initialize an empty list if JSON data is invalid
        except FileNotFoundError as e:
            print(f"File not found: {self.iofile_future.name}")
            self.future_list = []  # Initialize an empty list if the file doesn't exist

    def write_file(self):
        self.iofile.seek(0)
        self.iofile.truncate(0)
        json.dump(self.data_dict, self.iofile)

    def write_future_file(self):
        self.iofile_future.seek(0)
        self.iofile_future.truncate()
        self.new_future_list.sort(key=lambda x: x['when_to_process'], reverse=True)

        # Convert datetime objects to formatted strings
        serializable_data = [
            {
                'when_to_process': item['when_to_process'].strftime('%Y-%m-%d %H:%M:%S'),
                'time_entered': item['time_entered'].strftime('%Y-%m-%d %H:%M:%S'),
                'level': item['level']
            }
            for item in self.new_future_list
        ]

        json.dump(serializable_data, self.iofile_future, indent=4)

    def write_log(self, mg_to_add):
        log_mesg = (f'level is {round(self.data_dict["level"], 1)} '
                    f'at {self.data_dict["time"]}')
        if self.mg_net_change:
            mins_decayed = (self.current_time - self.when_to_process).total_seconds() / 60

            log_mesg = (f'{self.mg_net_change:.1f} mg added ({mg_to_add:.1f} '
                        f'mg, decayed {mins_decayed:.1f} mins): ' + log_mesg)
            logging.info(log_mesg)
        else:
            logging.debug(log_mesg)

    def decay_prev_level(self):
        """
        Reduce stored level to account for decay since that value
        was written
        """
        stored_time = datetime.strptime(self.data_dict['time'], '%Y-%m-%d %H:%M:%S')
        minutes_elapsed = (self.current_time - stored_time).total_seconds() / 60
        self.data_dict['time'] = self.current_time.strftime('%Y-%m-%d %H:%M:%S')
        self.data_dict['level'] *= pow(0.5, (minutes_elapsed / self.half_life))

    def decay_before_add(self):
        """
        Decay caffeine consumed some time ago
        before it gets added to current level.

        :return: net change rounded to 1 digit past decimal point
        Called by: process_item()
        """
        amt_to_decay_local = self.current_item['level']

        # calculate the time since this consumption
        minutes_elapsed = (self.current_time - self.current_item['when_to_process']).total_seconds() / 60
        amount_left_after_decay = amt_to_decay_local * pow(0.5, (minutes_elapsed / self.half_life))
        self.mg_net_change = round(amount_left_after_decay, 1)

    def add_caffeine(self, mg_to_add):
        """
        Called by: self.add_coffee()
        """
        if not self.mg_net_change:
            return
        self.data_dict['level'] += self.mg_net_change
        self.write_log(mg_to_add)

    def add_coffee(self):
        mg_to_add_now = self.mg_to_add / 4
        time_entered = self.current_time - timedelta(minutes=self.mins_ago)

        for i in range(4):
            item = {
                'when_to_process': time_entered + timedelta(minutes=i * COFFEE_MINS_DECREMENT),
                'time_entered': time_entered,
                'level': mg_to_add_now
            }
            self.future_list.append(item)

    def add_soda(self):
        mg_to_add_now = self.mg_to_add
        time_entered = self.current_time - timedelta(minutes=self.mins_ago)

        # First part (65%)
        item1 = {
            'when_to_process': time_entered,
            'time_entered': time_entered,
            'level': mg_to_add_now * 0.65
        }
        self.future_list.append(item1)

        # Second part (25%)
        item2 = {
            'when_to_process': time_entered + timedelta(minutes=SODA_MINS_DECREMENT),
            'time_entered': time_entered,
            'level': mg_to_add_now * 0.25
        }
        self.future_list.append(item2)

        # Third part (10%)
        item3 = {
            'when_to_process': time_entered + timedelta(minutes=2 * SODA_MINS_DECREMENT),
            'time_entered': time_entered,
            'level': mg_to_add_now * 0.1
        }
        self.future_list.append(item3)

    def process_future_list(self):
        self.future_list.sort(key=lambda x: x['when_to_process'], reverse=True)
        while self.future_list:
            self.current_item = self.future_list.pop()
            self.time_entered = self.current_item['time_entered']
            self.when_to_process = self.current_item['when_to_process']
            self.mg_net_change = self.current_item['level']
            self.process_item(self.current_item['level'])
        self.new_future_list.sort(key=lambda x: x['when_to_process'], reverse=True)

    def process_item(self, mg_to_add_local):
        if self.mg_net_change == 0:
            return

        # if self.time_entered >= self.current_time:
        #     raise ValueError("time_entered cannot be in the future")

        if self.when_to_process > self.current_time:  # item is still in the future
            new_item = {"when_to_process": self.when_to_process, "time_entered": self.time_entered,
                        "level": self.mg_net_change}
            self.new_future_list.append(new_item)
        elif self.when_to_process == self.current_time:  # item is in the present
            self.add_caffeine(mg_to_add_local)
        else:  # self.when_to_process < current_time:  # item is in the past
            self.mins_ago = (self.current_time - self.when_to_process).total_seconds() / 60
            self.decay_before_add()
            self.add_caffeine(mg_to_add_local)

    def update_time(self):
        """
        Called by: main()
        """
        self.data_dict['time'] = datetime.strftime(datetime.today(), '%Y-%m-%d %H:%M:%S')

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
