#!/usr/bin/env python3.7

# file: caffeine_monitor.py
# andrew jarcho
# 2019-10-08

# Answer question: how many mg of caffeine are in me now?


from datetime import datetime, timedelta
import sys
import json
from pathlib import Path


class CoffeeMonitor:
    half_life = 360  # in minutes

    def __init__(self, iofile, mg):
        self.iofile = iofile
        self.old_time = None
        self.level = None
        self.curr_time = None
        self.data_dict = {}
        self.mg_to_add = mg

    def main(self):
        self.read_file()
        self.decay()
        if self.mg_to_add:
            self.add_caffeine()
        self.update_time()
        self.write_file()
        print(self)

    def read_file(self):
        self.data_dict = json.load(self.iofile)
        old_time_float = self.data_dict['time']
        self.old_time = datetime.strptime(str(old_time_float),
                                          '%Y-%m-%d_%H:%M')
        level_str = self.data_dict['level']
        self.level = float(level_str)

    def write_file(self):
        self.iofile.seek(0)
        self.iofile.truncate(0)
        json.dump(self.data_dict, self.iofile)

    def decay(self):
        self.curr_time = datetime.today()
        minutes_elapsed = (self.curr_time -
                           self.old_time) / timedelta(minutes=1)
        self.data_dict['time'] = datetime.strftime(self.curr_time,
                                                   '%Y-%m-%d_%H:%M')
        self.level = self.level * pow(0.5, (minutes_elapsed / self.half_life))
        self.data_dict['level'] = self.level

    def add_caffeine(self):
        self.level += self.mg_to_add
        self.data_dict['level'] += self.mg_to_add

    def update_time(self):
        self.data_dict['time'] = datetime.strftime(datetime.today(),
                                                   '%Y-%m-%d_%H:%M')

    def __str__(self):
        return (f'Caffeine level is {round(self.level, 1)} mg at time '
                f'{self.data_dict["time"]}')


def init_storage(fname):
    outfile = open(fname, 'w')
    time_now = datetime.strftime(datetime.today(), '%Y-%m-%d_%H:%M')
    start_level = 0
    json.dump({"time": time_now, "level": start_level}, outfile)
    outfile.close()


if __name__ == '__main__':
    if len(sys.argv) > 2:
        print('Usage: program_name <mgs_of_caffeine_to_add>')
        sys.exit(0)

    filename = 'caffeine.json'
    my_file = Path(filename)
    if not my_file.is_file():
        init_storage(filename)
    with open(filename, 'r+') as storage:
        monitor = CoffeeMonitor(storage,
                                int(sys.argv[1]) if len(sys.argv) > 1 else 0)
        monitor.main()
