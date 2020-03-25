import pytest
from argparse import Namespace

from caffeine_monitor import CaffeineMonitor


def test_first(c_mon):
    nmspc = Namespace(mg=100, mins=180)
    cm = CaffeineMonitor(c_mon[1], nmspc.mg, nmspc.mins)
    assert isinstance(cm, CaffeineMonitor)


