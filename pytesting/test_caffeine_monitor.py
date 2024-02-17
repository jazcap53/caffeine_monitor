from argparse import Namespace
from datetime import datetime

from freezegun import freeze_time

from src.caffeine_monitor import CaffeineMonitor


def test_can_make_caffeine_monitor_instance(test_files):
    nmspc = Namespace(mg=100, mins=180, bev='coffee')
    cm = CaffeineMonitor(test_files[0], test_files[1], test_files[2], True, nmspc)
    assert isinstance(cm, CaffeineMonitor)
    assert cm.mg_to_add == 100
    assert cm.mins_ago == 180


def test_read_file(test_files):
    with open(test_files[1], 'r+') as j_file_handle:
        cm = CaffeineMonitor(j_file_handle, Namespace(mg=200, mins=360,
                                                      test=True))
        assert(isinstance(cm, CaffeineMonitor))
        cm.read_file()
        assert cm.data_dict['level'] == 48
        dt_out = datetime(2020, 4, 1, 12, 51)
        assert cm.data_dict['time'] == datetime.strftime(dt_out,
                                                         '%Y-%m-%d_%H:%M')


def test_write_file_add_mg(cm, test_files, caplog):
    with open(test_files[0], 'r+') as l_file_handle:
        cur_time = datetime.now().strftime('%Y-%m-%d_%H:%M')
        cm.data_dict = {'level': 140.0, 'time': cur_time}
        caplog.set_level('INFO')

        cm.mins_ago = 0
        cm.mg_to_add = 140
        cm.mg_net_change = 140.0

        cm.write_file()

        assert f'140.0 mg added (140 mg, 0 mins ago): level is 140.0 at {cur_time}' in caplog.text
        assert len(caplog.records) == 1


def test_write_file_add_no_mg(cm, test_files, caplog):
    with open(test_files[0], 'r+') as l_file_handle:
        cur_time = datetime.now().strftime('%Y-%m-%d_%H:%M')
        cm.data_dict = {'level': 140.0, 'time': cur_time}
        caplog.set_level('DEBUG')

        cm.write_file()

        assert f'level is 140.0 at {cur_time}' in caplog.text
        assert len(caplog.records) == 1


def test_decay_prev_level(cm):
    cm.read_file()  # loads cm.data_dict from file
    assert cm.data_dict['level'] == 48.0
    assert cm.data_dict['time'] == datetime(2020, 4, 1, 12, 51).strftime('%Y-%m-%d_%H:%M')
    freezer = freeze_time('2020-04-01 18:51')
    freezer.start()
    cm.decay_prev_level()
    freezer.stop()
    assert cm.data_dict['level'] == 24.0  # level decays by 50% in 6 hours
    assert cm.data_dict['time'] == datetime(2020, 4, 1, 18, 51).strftime('%Y-%m-%d_%H:%M')


def test_decay_before_add_360_mins_elapsed(cm):
    cm.read_file()  # loads cm.data_dict from file
    assert cm.data_dict['level'] == 48.0
    assert cm.data_dict['time'] == datetime(2020, 4, 1, 12, 51).strftime('%Y-%m-%d_%H:%M')
    cm.mg_to_add = 200
    cm.mins_ago = 360
    cm.mg_net_change = cm.decay_before_add()
    assert cm.mg_net_change == 100


def test_decay_before_add_0_mins_elapsed(cm):
    cm.read_file()  # loads cm.data_dict from file
    assert cm.data_dict['level'] == 48.0
    assert cm.data_dict['time'] == datetime(2020, 4, 1, 12, 51).strftime('%Y-%m-%d_%H:%M')
    cm.mg_to_add = 200
    cm.mins_ago = 0
    cm.decay_before_add()
    assert cm.mg_to_add == 200


def test_add_caffeine(cm):
    cm.read_file()  # loads cm.data_dict from file
    assert cm.data_dict['level'] == 48.0
    cm.mg_to_add = 12
    cm.add_caffeine()
    assert cm.data_dict['level'] == 60.0


def test_update_time(cm):
    cm.read_file()  # loads cm.data_dict from file
    assert cm.data_dict['time'] == datetime(2020, 4, 1, 12, 51).strftime('%Y-%m-%d_%H:%M')
    freezer = freeze_time('2020-05-01 11:00')
    freezer.start()
    cm.update_time()
    freezer.stop()
    assert cm.data_dict['time'] == '2020-05-01_11:00'


def test_str(cm):
    cm.read_file()  # loads cm.data_dict from file
    assert cm.data_dict['level'] == 48.0
    assert cm.data_dict['time'] == datetime(2020, 4, 1, 12, 51).strftime('%Y-%m-%d_%H:%M')
    assert str(cm) == 'Caffeine level is 48.0 mg at time 2020-04-01_12:51'


def test_main(cm, test_files, capsys):
    with open(test_files[1], 'r+') as j_file_handle:
        cm.iofile = j_file_handle
        cm.mg_to_add = 300
        cm.mins_ago = 360
        freezer = freeze_time('2020-04-01 18:51')
        freezer.start()
        cm.main()
        freezer.stop()
    assert capsys.readouterr()[0] == 'Caffeine level is 174.0 mg at time 2020-04-01_18:51\n'
