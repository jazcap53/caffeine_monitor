# file: caffeine_monitor.py
# andrew jarcho
# 2019-10-08

# Answer question: how many mg of caffeine are in me now?

# 1. read previous time and amount, if any, from file
# 2. report current time and amount
# 3. add a new amount (now or at some previous time)

from datetime import datetime, timedelta
# import math


class CoffeeMonitor:
    half_life = 360  # in minutes

    def __init__(self, iofile):
        self.iofile = iofile
        self.old_time = None
        self.level = None
        self.curr_time = None

    def read_file(self):
        try:
            old_time_str = self.iofile.readline().strip().lstrip('\x00')
            self.old_time = datetime.strptime(old_time_str, '%Y-%m-%d_%H:%M')
            level_str = self.iofile.readline().strip()
            self.level = float(level_str)
        except FileNotFoundError:
            self.old_time = datetime.today()
            self.level = 0.0

    def write_file(self):
        self.iofile.truncate(0)
        print(datetime.strftime(self.curr_time, '%Y-%m-%d_%H:%M'), file=self.iofile)
        print(self.level, file=self.iofile)

    def decay(self):
        self.curr_time = datetime.today()
        minutes_elapsed = (self.curr_time - self.old_time) / timedelta(minutes=1)
        # print(minutes_elapsed)
        self.level = self.level * pow(0.5, (minutes_elapsed / self.half_life))
        # print(self.level)

    def add_caffeine(self, amount):
        self.level += amount

    def __str__(self):
        return (f'Caffeine level is {int(round(self.level, 0))} mg at time '
                f'{datetime.strftime(self.old_time, "%Y-%m-%d %H:%M")}.')


if __name__ == '__main__':
    with open('caffeine.txt', 'r+') as storage:
        monitor = CoffeeMonitor(storage)
        monitor.read_file()
        print(monitor)
        monitor.decay()
        print(monitor)
        monitor.add_caffeine(16)
        print(monitor)
        monitor.write_file()
