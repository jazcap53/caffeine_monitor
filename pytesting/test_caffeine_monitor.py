# file: test_caffeine_monitor.py

from argparse import Namespace
from datetime import datetime, timedelta, MINYEAR

from freezegun import freeze_time
import json
import pytest
from pytest_mock import MockerFixture
import sys

from caffeine_monitor.src.caffeine_monitor import CaffeineMonitor


def test_can_make_caffeine_monitor_instance_mocked(files_mocked):
    """
    Check CaffeineMonitor ctor makes instance
    """
    open_mock, json_load_mock, json_dump_mock = files_mocked
    nmspc = Namespace(mg=100, mins=180, bev='coffee')
    cm_obj = CaffeineMonitor(open_mock, json_load_mock, json_load_mock, True, nmspc)
    assert isinstance(cm_obj, CaffeineMonitor)
    assert cm_obj.mg_to_add == 100
    assert cm_obj.mins_ago == 180


def test_can_make_caffeine_monitor_instance(files_mocked):
    """
    Check CaffeineMonitor ctor makes instance
    """
    open_mock, json_load_mock, json_dump_mock = files_mocked
    nmspc = Namespace(mg=100, mins=180, bev='coffee')
    cm_obj = CaffeineMonitor(open_mock, json_load_mock, json_load_mock, True, nmspc)
    assert isinstance(cm_obj, CaffeineMonitor)
    assert cm_obj.mg_to_add == 100
    assert cm_obj.mins_ago == 180


def test_read_file(files_mocked):
    """
    Check read_file() sets data_dict values
    """
    nmspc = Namespace(mg=100, mins=180, bev='coffee')
    open_mock, json_load_mock, json_dump_mock = files_mocked
    cm_obj = CaffeineMonitor(open_mock, json_load_mock, json_load_mock, True, nmspc)
    assert(isinstance(cm_obj, CaffeineMonitor))
    assert cm_obj.data_dict == {}
    cm_obj.read_file()
    assert cm_obj.data_dict['level'] == 0.0
    assert cm_obj.data_dict['time'] == datetime.now().strftime('%Y-%m-%d_%H:%M')


def test_write_file_add_mg(files_mocked, caplog):
    """
    Check add_caffeine() adds mg_net_change
    Check add_caffeine() writes correct value to log
    """
    nmspc = Namespace(mg=140, mins=0, bev='coffee')
    open_mock, json_load_mock, json_dump_mock = files_mocked
    cm_obj = CaffeineMonitor(open_mock, json_load_mock, json_load_mock, True, nmspc)
    cur_time = datetime.now().strftime('%Y-%m-%d_%H:%M')
    orig_level = 100.0

    cm_obj.data_dict = {'level': orig_level, 'time': cur_time}
    cm_obj.mg_net_change = cm_obj.mg_to_add
    caplog.set_level('INFO')

    cm_obj.add_caffeine()

    assert f'140.0 mg added (140 mg, 0 mins ago): level is {orig_level + cm_obj.mg_net_change} at {cur_time}' in caplog.text
    assert len(caplog.records) == 1


def test_add_no_mg_not_write_log(files_mocked, caplog):
    """
    Check adding 0 mg does not write to log
    """
    nmspc = Namespace(mg=0, mins=0, bev='coffee')
    open_mock, json_load_mock, json_dump_mock = files_mocked
    cm_obj = CaffeineMonitor(open_mock, json_load_mock, json_load_mock, True, nmspc)
    cur_time = datetime.now().strftime('%Y-%m-%d_%H:%M')
    cm_obj.data_dict = {'level': 200.0, 'time': cur_time}
    assert cm_obj.mg_to_add == 0.0
    caplog.set_level('DEBUG')

    cm_obj.add_caffeine()

    assert len(caplog.records) == 0


def test_add_no_mg_updates_time(files_mocked):
    """
    Check adding no mg updates the time in caff_test.json
    """
    nmspc = Namespace(mg=0, mins=0, bev='coffee')
    open_mock, json_load_mock, json_dump_mock = files_mocked

    initial_level = 50.0
    json_load_mock.side_effect = [
        {"time": "2020-04-01_12:51", "level": initial_level},
        []
    ]

    cm_obj = CaffeineMonitor(open_mock, json_load_mock, json_load_mock, False, nmspc)
    cur_time = datetime.now().strftime('%Y-%m-%d_%H:%M')
    cm_obj.data_dict = {"time": cur_time, "level": initial_level}

    expected = {"time": cur_time, "level": initial_level}
    cm_obj.write_file()

    json_dump_mock.assert_called_once_with(expected, cm_obj.iofile)
    

# @pytest.mark.skip(reason="research how to test this")
# def test_decay_prev_level(test_files, nmsp):
#
#     cm = CaffeineMonitor(test_files[0], test_files[1], test_files[2], True, nmsp)
#
#     # Set up known initial values
#     cm.data_dict = {'level': 48.0, 'time': '2020-04-01_12:51'}
#
#     # Freeze time and set cm.curr_time explicitly
#     freezer = freeze_time('2020-04-01 18:51')
#     freezer.start()
#     cm.curr_time = freezer.time
#
#     # Call method
#     cm.decay_prev_level()
#
#     # Assertions
#     assert cm.data_dict['level'] == 24.0
#     assert cm.data_dict['time'] == '2020-04-01_18:51'
#
#     freezer.stop()



# @pytest.mark.parametrize("initial_level, initial_time, time_elapsed, expected_level", [
#     (48.0, "2020-04-01_12:51", 360, 24.0),  # Normal case: 6 hours elapsed
#     (100.0, "2020-04-01_12:51", 0, 100.0),  # Edge case: 0 minutes elapsed
#     (300.0, "2020-04-01_12:51", 720, 75.0),  # Edge case: 12 hours elapsed
#     (0.0, "2020-04-01_12:51", 360, 0.0),  # Edge case: initial level is 0
# ])
# def test_decay_prev_level(files_mocked_with_initial_values, initial_level, initial_time, time_elapsed, expected_level,
#                           mocker):
#     open_mock, json_load_mock, json_dump_mock = files_mocked_with_initial_values
#
#     # Create a dynamic object with attributes 'mg', 'mins', and 'bev' to mimic argparse.Namespace
#     nmspc = type('Namespace', (), {'mg': 0, 'mins': 0, 'bev': 'coffee'})()
#
#     cm_obj = CaffeineMonitor(open_mock, json_load_mock, json_load_mock, False, nmspc)
#     cm_obj.data_dict = {"time": initial_time, "level": initial_level}
#
#     # Freeze the time and set the current time to be time_elapsed minutes later
#     with freeze_time(datetime.strptime(initial_time, '%Y-%m-%d_%H:%M') + timedelta(minutes=time_elapsed)):
#         cm_obj.decay_prev_level()
#
#     # Assert that the level in data_dict is correctly decayed
#     assert cm_obj.data_dict['level'] == pytest.approx(expected_level, abs=1e-6)
#
#     # Assert that the time in data_dict is updated correctly
#     assert cm_obj.data_dict['time'] == datetime.now().strftime('%Y-%m-%d_%H:%M')



# @pytest.mark.parametrize("initial_level, initial_time, time_elapsed, expected_level", [
#     (48.0, "2020-04-01_12:51", 360, 24.0),  # Normal case: 6 hours elapsed
#     (100.0, "2020-04-01_12:51", 0, 100.0),  # Edge case: 0 minutes elapsed
#     (300.0, "2020-04-01_12:51", 720, 75.0),  # Edge case: 12 hours elapsed
#     (0.0, "2020-04-01_12:51", 360, 0.0),  # Edge case: initial level is 0
# ])
# def test_decay_prev_level(files_mocked_with_initial_values, initial_level, initial_time, time_elapsed, expected_level,
#                           mocker):
#     open_mock, json_load_mock, json_dump_mock = files_mocked_with_initial_values
#
#     # Create a dynamic object with attributes 'mg', 'mins', and 'bev' to mimic argparse.Namespace
#     nmspc = type('Namespace', (), {'mg': 0, 'mins': 0, 'bev': 'coffee'})()
#
#     # Set the initial data_dict values based on the test case parameters
#     json_load_mock.return_value = {"time": initial_time, "level": initial_level}
#
#     cm_obj = CaffeineMonitor(open_mock, json_load_mock, json_load_mock, False, nmspc)
#     cm_obj.data_dict = json_load_mock.return_value  # Initialize data_dict
#
#     # Freeze the time and set the current time to be time_elapsed minutes later
#     with freeze_time(datetime.strptime(initial_time, '%Y-%m-%d_%H:%M') + timedelta(minutes=time_elapsed)):
#         cm_obj.decay_prev_level()
#
#     # Assert that the level in data_dict is correctly decayed
#     assert cm_obj.data_dict['level'] == pytest.approx(expected_level, abs=1e-6)
#
#     # Assert that the time in data_dict is updated correctly
#     assert cm_obj.data_dict['time'] == datetime.now().strftime('%Y-%m-%d_%H:%M')



# @pytest.mark.parametrize("initial_level, initial_time, time_elapsed, expected_level", [
#     (48.0, "2020-04-01_12:51", 360, 24.0),  # Normal case: 6 hours elapsed
#     (100.0, "2020-04-01_12:51", 0, 100.0),  # Edge case: 0 minutes elapsed
#     (300.0, "2020-04-01_12:51", 720, 75.0),  # Edge case: 12 hours elapsed
#     (0.0, "2020-04-01_12:51", 360, 0.0),  # Edge case: initial level is 0
# ])
# def test_decay_prev_level(files_mocked_with_initial_values, initial_level, initial_time, time_elapsed, expected_level,
#                           mocker):
#     open_mock, json_load_mock, json_dump_mock = files_mocked_with_initial_values
#
#     # Create a dynamic object with attributes 'mg', 'mins', and 'bev' to mimic argparse.Namespace
#     nmspc = type('Namespace', (), {'mg': 0, 'mins': 0, 'bev': 'coffee'})()
#
#     # Set the initial data_dict values based on the test case parameters
#     json_load_mock.return_value = {"time": initial_time, "level": initial_level}
#
#     cm_obj = CaffeineMonitor(open_mock, json_load_mock, json_load_mock, False, nmspc)
#     cm_obj.data_dict = json_load_mock.return_value  # Initialize data_dict
#
#     # Freeze the time and set the current time to be time_elapsed minutes later
#     with freeze_time(datetime.strptime(initial_time, '%Y-%m-%d_%H:%M') + timedelta(minutes=time_elapsed)):
#         cm_obj.decay_prev_level()
#
#     # Assert that the level in data_dict is correctly decayed
#     assert cm_obj.data_dict['level'] == pytest.approx(expected_level, abs=1e-6)
#
#     # Assert that the time in data_dict is updated correctly
#     assert cm_obj.data_dict['time'] == datetime.now().strftime('%Y-%m-%d_%H:%M')



# @pytest.mark.parametrize("initial_level, initial_time, time_elapsed, expected_level, mg, mins, bev", [
#     (48.0, "2020-04-01_12:51", 360, 24.0, 0, 0, 'coffee'),  # Normal case: 6 hours elapsed
#     (100.0, "2020-04-01_12:51", 0, 100.0, 100, 0, 'coffee'),  # Edge case: 0 minutes elapsed
#     (300.0, "2020-04-01_12:51", 720, 75.0, 300, 720, 'coffee'),  # Edge case: 12 hours elapsed
#     (0.0, "2020-04-01_12:51", 360, 0.0, 0, 360, 'coffee'),  # Edge case: initial level is 0
# ])
# def test_decay_prev_level(files_mocked_with_initial_values, initial_level, initial_time, time_elapsed, expected_level, mg, mins, bev, mocker):
#     open_mock, json_load_mock, json_dump_mock = files_mocked_with_initial_values
#
#     # Create a dynamic class to mimic argparse.Namespace
#     Namespace = type('Namespace', (), {'mg': mg, 'mins': mins, 'bev': bev})
#
#     # Create an instance of the dynamic class
#     nmspc = Namespace()
#
#     # Set the initial data_dict values based on the test case parameters
#     json_load_mock.return_value = {"time": initial_time, "level": initial_level}
#
#     cm_obj = CaffeineMonitor(open_mock, json_load_mock, json_load_mock, False, nmspc)
#     cm_obj.data_dict = json_load_mock.return_value  # Initialize data_dict
#
#     # Freeze the time and set the current time to be time_elapsed minutes later
#     with freeze_time(datetime.strptime(initial_time, '%Y-%m-%d_%H:%M') + timedelta(minutes=time_elapsed)):
#         cm_obj.decay_prev_level()
#
#     # Assert that the level in data_dict is correctly decayed
#     assert cm_obj.data_dict['level'] == pytest.approx(expected_level, abs=1e-6)
#
#     # Assert that the time in data_dict is updated correctly
#     assert cm_obj.data_dict['time'] == datetime.now().strftime('%Y-%m-%d_%H:%M')




# @pytest.mark.parametrize("initial_level, initial_time, time_elapsed, expected_level, mg, mins, bev", [
#     (48.0, "2020-04-01_12:51", 360, 24.0, 0, 0, 'coffee'),  # Normal case: 6 hours elapsed
#     (100.0, "2020-04-01_12:51", 0, 100.0, 100, 0, 'coffee'),  # Edge case: 0 minutes elapsed
#     (300.0, "2020-04-01_12:51", 720, 75.0, 300, 720, 'coffee'),  # Edge case: 12 hours elapsed
#     (0.0, "2020-04-01_12:51", 360, 0.0, 0, 360, 'coffee'),  # Edge case: initial level is 0
# ])
# def test_decay_prev_level(files_mocked_with_initial_values, initial_level, initial_time, time_elapsed, expected_level, mg, mins, bev, mocker):
#     open_mock, json_load_mock, json_dump_mock = files_mocked_with_initial_values
#
#     print(f'mg is {mg}')
#
#     # Create a dynamic class to mimic argparse.Namespace
#     TestNamespace = type('TestNamespace', (), {'mg': mg, 'mins': mins, 'bev': bev})
#
#     # Create an instance of the dynamic class
#     test_nmspc = TestNamespace()
#
#     print(f"test_nmspc.mg is {test_nmspc.mg}")
#
#     # Set the initial data_dict values based on the test case parameters
#     json_load_mock.return_value = {"time": initial_time, "level": initial_level}
#     print(f"json_load_mock.return_value['level'] is {json_load_mock.return_value['level']}")
#
#     cm_obj = CaffeineMonitor(open_mock, json_load_mock, json_load_mock, False, test_nmspc)
#     print(f"cm_obj.data_dict is originally {cm_obj.data_dict}")
#
#     cm_obj.data_dict = json_load_mock.return_value  # Initialize data_dict
#     print(f"initialized cm_obj.data_dict is {cm_obj.data_dict}")
#
#
#     # Freeze the time and set the current time to be time_elapsed minutes later
#     with freeze_time(datetime.strptime(initial_time, '%Y-%m-%d_%H:%M') + timedelta(minutes=time_elapsed)):
#         cm_obj.decay_prev_level()
#
#     # Assert that the level in data_dict is correctly decayed
#     assert cm_obj.data_dict['level'] == pytest.approx(expected_level, abs=1e-6)
#
#     # Assert that the time in data_dict is updated correctly
#     assert cm_obj.data_dict['time'] == datetime.now().strftime('%Y-%m-%d_%H:%M')



@pytest.mark.parametrize("initial_level, initial_time, time_elapsed, expected_level, mg, mins, bev", [
    (48.0, "2020-04-01_12:51", 360, 24.0, 0, 0, 'coffee'),  # Normal case: 6 hours elapsed
    (100.0, "2020-04-01_12:51", 0, 100.0, 100, 0, 'coffee'),  # Edge case: 0 minutes elapsed
    (300.0, "2020-04-01_12:51", 720, 75.0, 300, 720, 'coffee'),  # Edge case: 12 hours elapsed
    (0.0, "2020-04-01_12:51", 360, 0.0, 0, 360, 'coffee'),  # Edge case: initial level is 0
])
def test_decay_prev_level(files_mocked_with_initial_values, initial_level, initial_time, time_elapsed, expected_level, mg, mins, bev, mocker):
    open_mock, json_load_mock, json_dump_mock = files_mocked_with_initial_values

    # Create a dynamic class to mimic argparse.Namespace
    TestNamespace = type('TestNamespace', (), {'mg': mg, 'mins': mins, 'bev': bev})

    # Create an instance of the dynamic class
    nmspc = TestNamespace()

    # Set the initial data_dict values based on the test case parameters
    json_load_mock.return_value = {"time": initial_time, "level": initial_level}

    cm_obj = CaffeineMonitor(open_mock, json_load_mock, json_load_mock, False, nmspc)
    cm_obj.data_dict = json_load_mock.return_value  # Initialize data_dict

    # Freeze the time before adding the time_elapsed delta
    frozen_time = datetime.strptime(initial_time, '%Y-%m-%d_%H:%M')
    with freeze_time(frozen_time):
        # Set the current time to be time_elapsed minutes later
        cm_obj.curr_time = frozen_time + timedelta(minutes=time_elapsed)
        cm_obj.decay_prev_level()

    # Assert that the level in data_dict is correctly decayed
    assert cm_obj.data_dict['level'] == pytest.approx(expected_level, abs=1e-6)

    # Assert that the time in data_dict is updated correctly
    assert cm_obj.data_dict['time'] == (frozen_time + timedelta(minutes=time_elapsed)).strftime('%Y-%m-%d_%H:%M')



@pytest.mark.parametrize("mg_add, min_ago, net_ch", [
    # Normal cases
    (200, 360, 100.0),
    (100, 180, 70.7),
    (300, 720, 75.0),

    # Edge cases
    (0, 0, 0.0),  # Adding 0 mg
    (200, 0, 200.0),  # Adding caffeine just now (min_ago = 0)
    (200, -60, 224.5),  # Adding caffeine in the future (min_ago < 0)
    (200, 720000, 0.0),  # Adding caffeine a very long time ago (practically decayed to 0)
    (sys.maxsize, 360, sys.maxsize / 2),  # Adding a very large amount of caffeine
])
def test_decay_before_add(files_mocked, mg_add, min_ago, net_ch):
    nmspc = Namespace(mg=mg_add, mins=min_ago, bev='coffee')
    open_mock, json_load_mock, json_dump_mock = files_mocked
    cm_obj = CaffeineMonitor(open_mock, json_load_mock, json_load_mock, False, nmspc)
    cm_obj.data_dict = {'level': 0.0, 'time': datetime(2020, 4, 1, 12, 51).strftime('%Y-%m-%d_%H:%M')}
    cm_obj.decay_before_add()
    assert cm_obj.mg_net_change == pytest.approx(net_ch, abs=1e-6)


# def test_add_coffee(mocker, files_mocked):
#     open_mock, json_load_mock, json_dump_mock = files_mocked
#     nmspc = Namespace(mg=100, mins=180, bev='coffee')
#     cm_obj = CaffeineMonitor(open_mock, json_load_mock, json_load_mock, True, nmspc)
#
#     # Mock the process_item method
#     mocker.patch.object(cm_obj, 'process_item')
#
#     cm_obj.add_coffee()
#
#     assert cm_obj.mg_net_change == 25
#     assert cm_obj.process_item.call_count == 4
#     assert cm_obj.mins_ago == 120


@pytest.mark.parametrize("mg, mins, expected_mg_net_change, expected_mins_ago", [
    (100, 180, 25, 120),    # Normal case
    (0, 0, 0, -60),         # Edge case: 0 mg and 0 mins
    (200, 0, 50, -60),      # Edge case: mins_ago is 0
    (100, -30, 25, -90),    # Edge case: negative mins_ago
])
def test_add_coffee(mocker, files_mocked, mg, mins, expected_mg_net_change, expected_mins_ago):
    open_mock, json_load_mock, json_dump_mock = files_mocked
    nmspc = Namespace(mg=mg, mins=mins, bev='coffee')
    cm_obj = CaffeineMonitor(open_mock, json_load_mock, json_load_mock, True, nmspc)

    mocker.patch.object(cm_obj, 'process_item')

    cm_obj.add_coffee()

    assert cm_obj.mg_net_change == expected_mg_net_change
    assert cm_obj.process_item.call_count == 4
    assert cm_obj.mins_ago == expected_mins_ago


@pytest.mark.parametrize("mg, mins, expected_mg_net_change, expected_mins_ago", [
    (200, 0, 20, -40),      # Normal case
    (0, 0, 0, -40),         # Edge case: 0 mg and 0 mins
    (300, 30, 30, -10),     # Edge case: mins_ago should be 30 - 40 = -10
    (100, -20, 10, -60),    # Edge case: mins_ago should be -20 - 40 = -60
])
def test_add_soda(mocker, files_mocked, mg, mins, expected_mg_net_change, expected_mins_ago):
    open_mock, json_load_mock, json_dump_mock = files_mocked
    nmspc = Namespace(mg=mg, mins=mins, bev='soda')
    cm_obj = CaffeineMonitor(open_mock, json_load_mock, json_load_mock, True, nmspc)

    mocker.patch.object(cm_obj, 'process_item')

    cm_obj.add_soda()

    assert cm_obj.mg_net_change == expected_mg_net_change
    assert cm_obj.process_item.call_count == 3
    assert cm_obj.mins_ago == expected_mins_ago


def test_add_caffeine(files_mocked):
    """Test add_caffeine() correctly updates data_dict['level']."""
    open_mock, json_load_mock, json_dump_mock = files_mocked
    nmspc = Namespace(mg=100, mins=0, bev='coffee')
    cm_obj = CaffeineMonitor(open_mock, json_load_mock, json_load_mock, True, nmspc)
    cm_obj.data_dict = {"time": "2020-04-01_12:51", "level": 48.0}
    orig_level = cm_obj.data_dict['level']
    cm_obj.mg_net_change = 100.0

    cm_obj.add_caffeine()

    assert cm_obj.data_dict['level'] == orig_level + cm_obj.mg_net_change


def test_update_time(files_mocked):
    nmspc = Namespace(mg=20, mins=20, bev='coffee')
    open_mock, json_load_mock, json_dump_mock = files_mocked
    cm_obj = CaffeineMonitor(open_mock, json_load_mock, json_load_mock, True, nmspc)
    cm_obj.read_file()  # loads cm.data_dict from file
    cm_obj.data_dict['time'] = (datetime.now() - timedelta(days=10)).strftime('%Y-%m-%d_%H:%M')
    freezer = freeze_time('2020-05-01 11:00')
    freezer.start()
    cm_obj.update_time()
    freezer.stop()
    assert cm_obj.data_dict['time'] == '2020-05-01_11:00'


def test_str(files_mocked):
    open_mock, json_load_mock, json_dump_mock = files_mocked
    nmspc = Namespace(mg=50, mins=50, bev='soda')
    cm_obj = CaffeineMonitor(open_mock, json_load_mock, json_load_mock, False, nmspc)
    cm_obj.data_dict['level'] = 48.0
    cm_obj.data_dict['time'] = datetime(2020, 4, 1, 12, 51).strftime('%Y-%m-%d_%H:%M')
    assert str(cm_obj) == 'Caffeine level is 48.0 mg at time 2020-04-01_12:51'


def test_read_log(files_mocked):
    nmspc = Namespace(mg=100, mins=0, bev='soda')
    open_mock, json_load_mock, json_dump_mock = files_mocked
    # open_mock below must be called; cm_obj.read_log iterates over list
    cm_obj = CaffeineMonitor(open_mock(), json_load_mock, json_load_mock, True, nmspc)
    cm_obj.read_log()
    assert cm_obj.log_contents[0] == 'Start of log file'
    assert cm_obj.log_contents[1] != cm_obj.log_contents[0]
    assert cm_obj.log_contents[2] == 1


def test_read_future_file(files_mocked):
    open_mock, json_load_mock, json_dump_mock = files_mocked

    # Define the expected future list
    expected_future_list = [{"time": "2023-06-08_10:00", "level": 50.0},
                            {"time": "2023-06-08_11:00", "level": 25.0}]

    # Configure the mock file to return the expected future list when json.load() is called
    json_load_mock.side_effect = [expected_future_list]

    # Create an instance of CaffeineMonitor with the mocked files
    nmspc = Namespace(mg=100, mins=180, bev='coffee')
    cm_obj = CaffeineMonitor(open_mock, json_load_mock, json_load_mock, True, nmspc)

    # Call the read_future_file() method
    cm_obj.read_future_file()

    # Assert that the future_list attribute is set correctly
    assert cm_obj.future_list == expected_future_list


def test_write_future_file(files_mocked):
    open_mock, json_load_mock, json_dump_mock = files_mocked

    # Create an instance of CaffeineMonitor with the mocked files
    nmspc = Namespace(mg=100, mins=180, bev='coffee')
    cm_obj = CaffeineMonitor(open_mock, json_load_mock, json_dump_mock, True, nmspc)

    # Set the new_future_list attribute with some test data
    cm_obj.new_future_list = [{"time": "2023-06-08_12:00", "level": 75.0},
                              {"time": "2023-06-08_13:00", "level": 30.0}]

    # Call the write_future_file() method
    cm_obj.write_future_file()

    # Assert that json.dump() is called with the correct arguments
    json_dump_mock.assert_called_once_with(cm_obj.new_future_list, cm_obj.iofile_future, indent=4)


@pytest.mark.skip(reason="test sub-method calls separately")
def test_main(files_mocked):
    """
    Test the main() method of the CaffeineMonitor class.

    This test verifies that the main() method correctly calculates and updates the caffeine level,
    accounting for the decay over time, and logs the changes appropriately.
    """
    nmspc = Namespace(mg=300, mins=360, bev='coffee')
    open_mock, json_load_mock, json_dump_mock = files_mocked

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
