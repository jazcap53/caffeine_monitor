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
        self.data_dict = {}
        self.mg_to_add = mg

    def main(self):
        self.data_dict = self.read_file()
        self.decay()
        if self.mg_to_add:
            self.add_caffeine()
        self.update_time()
        self.write_file()
        print(self)

    def read_file(self):
        data_dict = json.load(self.iofile)
        data_dict['time'] = datetime.strptime(data_dict['time'],
                                              '%Y-%m-%d_%H:%M')
        data_dict['level'] = float(data_dict['level'])
        self.data_dict = data_dict
        return self.data_dict

    def write_file(self):
        self.iofile.seek(0)
        self.iofile.truncate(0)
        json.dump(self.data_dict, self.iofile)
        return self.data_dict

    def decay(self):
        curr_time = datetime.today()
        old_time = self.data_dict['time']
        minutes_elapsed = (curr_time -
                           old_time) / timedelta(minutes=1)
        self.data_dict['time'] = datetime.strftime(curr_time,
                                                   '%Y-%m-%d_%H:%M')
        self.data_dict['level'] *= pow(0.5, (minutes_elapsed / self.half_life))
        return self.data_dict

    def add_caffeine(self):
        self.data_dict['level'] += self.mg_to_add
        return self.data_dict

    def update_time(self):
        self.data_dict['time'] = datetime.strftime(datetime.today(),
                                                   '%Y-%m-%d_%H:%M')
        return self.data_dict

    def __str__(self):
        return (f'Caffeine level is {round(self.data_dict["level"], 1)}'
                f' mg at time {self.data_dict["time"]}')


if __name__ == '__main__':
    if len(sys.argv) > 2:
        print('Usage: program_name <mgs_of_caffeine_to_add>')
        sys.exit(0)

    filename = 'caffeine_tester.json'
    my_file = Path(filename)
    if not my_file.is_file():
        outfile = open(filename, 'w')
        time_now = datetime.strftime(datetime.today(), '%Y-%m-%d_%H:%M')
        start_level = 0
        json.dump({"time": time_now, "level": start_level}, outfile)
        outfile.close()
    with open(filename, 'r+') as storage:
        monitor = CoffeeMonitor(storage,
                                int(sys.argv[1]) if len(sys.argv) > 1 else 0)
        monitor.main()
