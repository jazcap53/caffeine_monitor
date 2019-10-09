#!/usr/bin/env python3.7

# file: caffeine_monitor.py
# andrew jarcho
# 2019-10-08

# Answer question: how many mg of caffeine are in me now?

# 1. read previous time and amount, if any, from file
# 2. report current time and amount
# 3. add a new amount (now or at some previous time)


from datetime import datetime, timedelta
# import math
import json


class CoffeeMonitor:
    half_life = 360  # in minutes

    def __init__(self, iofile):
        self.iofile = iofile
        self.old_time = None
        self.level = None
        self.curr_time = None
        self.data_dict = {}

    def show_menu(self):
        self.read_file()
        self.decay()
        new_caffeine = int(input('Enter an (integer) amount of caffeine to add'
                                 ' (in mg), or enter "0" to read current'
                                 ' level:\n'))
        if new_caffeine:
            self.add_caffeine(new_caffeine)
        self.update_time()
        self.write_file()
        print(self)

    def read_file(self):
        self.data_dict = json.load(self.iofile)
        old_time_float = self.data_dict['time']
        self.old_time = datetime.strptime(str(old_time_float), '%Y-%m-%d_%H:%M')
        level_str = self.data_dict['level']
        self.level = float(level_str)

    def write_file(self):
        self.iofile.seek(0)
        self.iofile.truncate(0)
        json.dump(self.data_dict, self.iofile)

    def decay(self):
        self.curr_time = datetime.today()
        minutes_elapsed = (self.curr_time - self.old_time) / timedelta(minutes=1)
        self.data_dict['time'] = datetime.strftime(self.curr_time, '%Y-%m-%d_%H:%M')
        self.level = self.level * pow(0.5, (minutes_elapsed / self.half_life))
        self.data_dict['level'] = self.level

    def add_caffeine(self, amount):
        self.level += amount
        self.data_dict['level'] += amount

    def update_time(self):
        self.data_dict['time'] = datetime.strftime(datetime.today(), '%Y-%m-%d_%H:%M')

    def __str__(self):
        return (f'Caffeine level is {round(self.level, 1)} mg at time '
                f'{self.data_dict["time"]}')


if __name__ == '__main__':
    with open('caffeine.json', 'r+') as storage:
        monitor = CoffeeMonitor(storage)
        monitor.show_menu()
