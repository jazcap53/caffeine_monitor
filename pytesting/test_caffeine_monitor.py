# file: test_caffeine_monitor.py

from argparse import Namespace
from datetime import datetime, timedelta

from freezegun import freeze_time
import json
import pytest

from caffeine_monitor.src.caffeine_monitor import CaffeineMonitor


def test_can_make_caffeine_monitor_instance_mocked(files_mocked):
    """
    Check CaffeineMonitor ctor makes instance
    """
    open_mock, json_load_mock = files_mocked
    nmspc = Namespace(mg=100, mins=180, bev='coffee')
    cm_obj = CaffeineMonitor(open_mock(), open_mock(), open_mock(), True, nmspc)
    assert isinstance(cm_obj, CaffeineMonitor)
    assert cm_obj.mg_to_add == 100
    assert cm_obj.mins_ago == 180


def test_can_make_caffeine_monitor_instance(files_mocked):
    """
    Check CaffeineMonitor ctor makes instance
    """
    open_mock, json_load_mock = files_mocked
    nmspc = Namespace(mg=100, mins=180, bev='coffee')
    cm_obj = CaffeineMonitor(open_mock(), open_mock(), open_mock(), True, nmspc)
    assert isinstance(cm_obj, CaffeineMonitor)
    assert cm_obj.mg_to_add == 100
    assert cm_obj.mins_ago == 180


def test_read_file(files_mocked):
    """
    Check read_file() sets data_dict values
    """
    nmspc = Namespace(mg=100, mins=180, bev='coffee')
    open_mock, json_load_mock = files_mocked
    cm_obj = CaffeineMonitor(open_mock(), open_mock(), open_mock(), True, nmspc)
    assert(isinstance(cm_obj, CaffeineMonitor))
    assert cm_obj.data_dict == {}
    cm_obj.read_file()
    assert cm_obj.data_dict['level'] == 0.0
    assert cm_obj.data_dict['time'] == datetime.now().strftime('%Y-%m-%d_%H:%M')


def test_write_file_add_mg(pytesting_files, caplog):
    """
    Check add_caffeine() adds mg_net_change
    Check add_caffeine() writes correct value to log
    """
    nmspc = Namespace(mg=140, mins=0, bev='coffee')
    cm_obj = CaffeineMonitor(*pytesting_files, True, nmspc)
    cur_time = datetime.now().strftime('%Y-%m-%d_%H:%M')
    orig_level = 100.0

    cm_obj.data_dict = {'level': orig_level, 'time': cur_time}
    cm_obj.mg_net_change = cm_obj.mg_to_add
    caplog.set_level('INFO')

    cm_obj.add_caffeine()

    assert f'140.0 mg added (140 mg, 0 mins ago): level is {orig_level + cm_obj.mg_net_change} at {cur_time}' in caplog.text
    assert len(caplog.records) == 1


def test_add_no_mg_not_write_log(pytesting_files, caplog):
    """
    Check adding 0 mg does not write to log
    """
    nmspc = Namespace(mg=0, mins=0, bev='coffee')
    cm_obj = CaffeineMonitor(*pytesting_files, True, nmspc)
    cur_time = datetime.now().strftime('%Y-%m-%d_%H:%M')
    cm_obj.data_dict = {'level': 200.0, 'time': cur_time}
    assert cm_obj.mg_to_add == 0.0
    caplog.set_level('DEBUG')

    cm_obj.add_caffeine()

    assert len(caplog.records) == 0


def test_add_no_mg_updates_time(pytesting_files):
    """
    Check adding no mg updates caff_test.json
    """
    nmspc = Namespace(mg=0, mins=0, bev='coffee')
    caff_test_json_file = pytesting_files[1]
    caff_test_json_file.seek(0)
    caff_test_json_file.truncate(0)
    initial_data = {"time": "2020-04-01_12:51", "level": 50.0}
    json.dump(initial_data, caff_test_json_file)
    caff_test_json_file.seek(0)
    initial_data_from_file = json.load(caff_test_json_file)
    assert initial_data_from_file == initial_data
    cm_obj = CaffeineMonitor(*pytesting_files, False, nmspc)
    cur_time = datetime.now().strftime('%Y-%m-%d_%H:%M')
    cm_obj.data_dict = {"time": cur_time, "level": initial_data["level"]}
    cm_obj.write_file()
    cm_obj.iofile.seek(0)
    final_data_from_file = json.load(cm_obj.iofile)
    assert final_data_from_file == {"time": cur_time, "level": initial_data["level"]}


@pytest.mark.skip(reason="research how to test this")
def test_decay_prev_level(test_files, nmsp):

    cm = CaffeineMonitor(test_files[0], test_files[1], test_files[2], True, nmsp)

    # Set up known initial values
    cm.data_dict = {'level': 48.0, 'time': '2020-04-01_12:51'}

    # Freeze time and set cm.curr_time explicitly
    freezer = freeze_time('2020-04-01 18:51')
    freezer.start()
    cm.curr_time = freezer.time

    # Call method
    cm.decay_prev_level()

    # Assertions
    assert cm.data_dict['level'] == 24.0
    assert cm.data_dict['time'] == '2020-04-01_18:51'

    freezer.stop()


def test_decay_before_add_360_mins_elapsed(pytesting_files):
    nmspc = Namespace(mg=100, mins=180, bev='coffee')
    cm_obj = CaffeineMonitor(*pytesting_files, False, nmspc)
    cm_obj.data_dict = {'level': 48.0, 'time': datetime(2020, 4, 1, 12, 51).strftime('%Y-%m-%d_%H:%M')}
    assert cm_obj.data_dict['level'] == 48.0
    assert cm_obj.data_dict['time'] == datetime(2020, 4, 1, 12, 51).strftime('%Y-%m-%d_%H:%M')
    cm_obj.mg_to_add = 200
    cm_obj.mins_ago = 360
    cm_obj.decay_before_add()
    assert cm_obj.mg_net_change == 100


def test_decay_before_add_0_mins_elapsed(files_mocked):
    nmspc = Namespace(mg=100, mins=180, bev='coffee')
    open_mock, json_load_mock = files_mocked
    cm_obj = CaffeineMonitor(open_mock(), open_mock(), open_mock(), True, nmspc)
    cm_obj.read_file()  # loads cm.data_dict from file
    assert cm_obj.data_dict['level'] == 0.0
    assert cm_obj.data_dict['time'] == datetime.now().strftime('%Y-%m-%d_%H:%M')
    cm_obj.mg_to_add = 200
    cm_obj.mins_ago = 0
    cm_obj.decay_before_add()
    assert cm_obj.mg_to_add == 200


def test_decay_before_add_mins_ago_zero(files_mocked):
    """Test decay_before_add() when mins_ago is 0."""
    open_mock, json_load_mock = files_mocked
    nmspc = Namespace(mg=100, mins=0, bev='coffee')
    cm_obj = CaffeineMonitor(open_mock(), open_mock(), open_mock(), True, nmspc)
    cm_obj.data_dict = {"time": "2020-04-01_12:51", "level": 48.0}

    cm_obj.decay_before_add()

    assert cm_obj.mg_net_change == cm_obj.mg_to_add


def test_add_caffeine(files_mocked):
    """Test add_caffeine() correctly updates data_dict['level']."""
    open_mock, json_load_mock = files_mocked
    nmspc = Namespace(mg=100, mins=0, bev='coffee')
    cm_obj = CaffeineMonitor(open_mock(), open_mock(), open_mock(), True, nmspc)
    cm_obj.data_dict = {"time": "2020-04-01_12:51", "level": 48.0}
    orig_level = cm_obj.data_dict['level']
    cm_obj.mg_net_change = 100.0

    cm_obj.add_caffeine()

    assert cm_obj.data_dict['level'] == orig_level + cm_obj.mg_net_change


def test_update_time(files_mocked):
    nmspc = Namespace(mg=20, mins=20, bev='coffee')
    open_mock, json_load_mock = files_mocked
    cm_obj = CaffeineMonitor(open_mock(), open_mock(), open_mock(), True, nmspc)
    cm_obj.read_file()  # loads cm.data_dict from file
    cm_obj.data_dict['time'] = (datetime.now() - timedelta(days=10)).strftime('%Y-%m-%d_%H:%M')
    freezer = freeze_time('2020-05-01 11:00')
    freezer.start()
    cm_obj.update_time()
    freezer.stop()
    assert cm_obj.data_dict['time'] == '2020-05-01_11:00'


def test_str(files_mocked):
    open_mock, json_load_mock = files_mocked
    nmspc = Namespace(mg=50, mins=50, bev='soda')
    cm_obj = CaffeineMonitor(open_mock(), open_mock(), open_mock(), False, nmspc)
    cm_obj.data_dict['level'] = 48.0
    cm_obj.data_dict['time'] = datetime(2020, 4, 1, 12, 51).strftime('%Y-%m-%d_%H:%M')
    assert str(cm_obj) == 'Caffeine level is 48.0 mg at time 2020-04-01_12:51'


def test_read_log(files_mocked):
    nmspc = Namespace(mg=100, mins=0, bev='soda')
    open_mock, json_load_mock = files_mocked
    cm_obj = CaffeineMonitor(open_mock(), open_mock(), open_mock(), True, nmspc)
    cm_obj.read_log()
    assert cm_obj.log_contents[0] == 'Start of log file'
    assert cm_obj.log_contents[1] != cm_obj.log_contents[0]
    assert cm_obj.log_contents[2] == 1


@pytest.mark.skip(reason="test sub-method calls separately")
def test_main(files_mocked):
    """
    Test the main() method of the CaffeineMonitor class.

    This test verifies that the main() method correctly calculates and updates the caffeine level,
    accounting for the decay over time, and logs the changes appropriately.
    """
    nmspc = Namespace(mg=300, mins=360, bev='coffee')
    open_mock, json_load_mock = files_mocked

    log_file, json_file, json_future_file = files_mocked

    # Initialize the input JSON file with initial values
    initial_data = {"time": "2020-04-01_12:51", "level": 48.0}
    json.dump(initial_data, json_file)
    json_file.seek(0)

    # Initialize the future JSON file as an empty list
    json.dump([], json_future_file)
    json_future_file.seek(0)

    freezer = freeze_time('2020-04-01 18:51')
    freezer.start()

    cm_obj = CaffeineMonitor(open_mock(), open_mock(), open_mock(),True, nmspc)
    cm_obj.main()
    main_output = str(cm_obj)

    freezer.stop()

    assert main_output == 'Caffeine level is 120.6 mg at time 2020-04-01_18:51'
    log_file.seek(0)
    log_content = log_file.read()
    assert '120.6 mg added (300 mg, 360 mins ago): level is 120.6 at 2020-04-01_18:51' in log_content