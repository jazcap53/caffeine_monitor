# file: caffeine_monitor.py
# andrew jarcho
# 2019-10-08

# Answer question: how many mg of caffeine are in me now?

# 1. read previous time and amount, if any, from file
# 2. report current time and amount
# 3. add a new amount (now or at some previous time)

from datetime import datetime, timedelta
import math


class CoffeeMonitor:
    half_life = 360  # in minutes

    def __init__(self, infile):
        self.infile = infile
        self.old_time = None
        self.level = None

    def read_file(self):
        try:
            old_time_str = infile.readline().strip()
            self.old_time = datetime.strptime(old_time_str, '%Y-%m-%d_%H:%M')
            level_str = infile.readline().strip()
            self.level = float(level_str)
        except FileNotFoundError:
            self.old_time = datetime.today()
            self.level = 0.0
    
    def decay(self):
        self.curr_time = datetime.today()
        minutes_elapsed = (self.curr_time - self.old_time) / timedelta(minutes=1)
        print(minutes_elapsed)
        self.level = self.level * pow(0.5, (minutes_elapsed / self.half_life))
        print(self.level)

    def __str__(self):
        return (f'Caffeine level is {self.level} mg at time '
                f'{datetime.strftime(self.old_time, "%Y-%m-%d %H:%M")}.')


if __name__ == '__main__':
    with open('caffeine.txt', 'r') as infile:
        monitor = CoffeeMonitor(infile)
        monitor.read_file()
        print(monitor)
        monitor.decay()

