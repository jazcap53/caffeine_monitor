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

    def read_file(self):
        try:
            self.data_dict = json.load(self.iofile)
            old_time_float = self.data_dict['time']
            self.old_time = datetime.strptime(str(old_time_float), '%Y-%m-%d_%H:%M')
            level_str = self.data_dict['level']
            self.level = float(level_str)
        except FileNotFoundError:
            self.old_time = datetime.today()
            self.level = 0.0

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

    def __str__(self):
        return (f'Caffeine level is {round(self.level, 1)} mg at time '
                f'{datetime.strftime(self.old_time, "%Y-%m-%d %H:%M")}')


if __name__ == '__main__':
    with open('caffeine.json', 'r+') as storage:
        monitor = CoffeeMonitor(storage)
        monitor.read_file()
        monitor.decay()
        # monitor.add_caffeine(16)
        # print(monitor)
        monitor.write_file()
        print(monitor)
