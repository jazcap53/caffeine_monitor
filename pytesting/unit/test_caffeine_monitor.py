# file: pytesting/test_caffeine_monitor.py

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
    assert cm_obj.data_dict['time'] == datetime.now().strftime('%Y-%m-%d %H:%M:%S')


@pytest.mark.parametrize("mg_to_add, mins", [
    (100, 0),     # Normal case
    (0, 0),       # Edge case: 0 mg and 0 mins
    (200, -60),   # Edge case: negative mins
    (50, 1440),   # Edge case: large positive mins (1 day)
    (-50, 0),     # Edge case: negative mg_to_add
    (-100, -30),  # Edge case: negative mg_to_add and negative mins
])
@pytest.mark.parametrize("bev", ['coffee', 'soda', 'chocolate'])
def test_write_file_add_mg(files_mocked, caplog, mg_to_add, mins, bev):
    """
    Check add_caffeine() adds mg_net_change
    Check add_caffeine() writes correct value to log
    """
    nmspc = Namespace(mg=mg_to_add, mins=mins, bev=bev)
    open_mock, json_load_mock, json_dump_mock = files_mocked
    cm_obj = CaffeineMonitor(open_mock, json_load_mock, json_load_mock, True, nmspc)
    cur_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    orig_level = 100.0

    cm_obj.data_dict = {'level': orig_level, 'time': cur_time}
    cm_obj.mg_net_change = mg_to_add
    caplog.set_level('INFO')

    cm_obj.add_caffeine(mg_to_add)

    if mg_to_add != 0:
        log_message = f'{mg_to_add:.1f} mg added ({mg_to_add:.1f} mg, decayed {mins:.1f} mins): level is {orig_level + cm_obj.mg_net_change} at {cur_time}'
        assert log_message in caplog.text
        assert len(caplog.records) == 1
    else:
        assert len(caplog.records) == 0

    assert cm_obj.data_dict['level'] == orig_level + cm_obj.mg_net_change


def test_add_no_mg_updates_time(files_mocked):
    """
    Check adding no mg updates the time in caff_test.json
    """
    nmspc = Namespace(mg=0, mins=0, bev='coffee')
    open_mock, json_load_mock, json_dump_mock = files_mocked

    initial_level = 50.0
    json_load_mock.side_effect = [
        {"time": "2020-04-01 12:51:00", "level": initial_level},
        []
    ]

    cm_obj = CaffeineMonitor(open_mock, json_load_mock, json_load_mock, False, nmspc)
    cur_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    cm_obj.data_dict = {"time": cur_time, "level": initial_level}

    expected = {"time": cur_time, "level": initial_level}
    cm_obj.write_file()

    json_dump_mock.assert_called_once_with(expected, cm_obj.iofile)


@pytest.mark.parametrize("initial_level, initial_time, time_elapsed, expected_level, mg, mins, bev", [
    (48.0, "2020-04-01 12:51:00", 360, 24.0, 0, 0, 'coffee'),  # Normal case: 6 hours elapsed
    (100.0, "2020-04-01 12:51:00", 0, 100.0, 100, 0, 'coffee'),  # Edge case: 0 minutes elapsed
    (300.0, "2020-04-01 12:51:00", 720, 75.0, 300, 720, 'coffee'),  # Edge case: 12 hours elapsed
    (0.0, "2020-04-01 12:51:00", 360, 0.0, 0, 360, 'coffee'),  # Edge case: initial level is 0
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
    frozen_time = datetime.strptime(initial_time, '%Y-%m-%d %H:%M:%S')
    with freeze_time(frozen_time):
        # Set the current_time to be time_elapsed minutes later
        cm_obj.current_time = frozen_time + timedelta(minutes=time_elapsed)
        cm_obj.decay_prev_level()

    # Assert that the level in data_dict is correctly decayed
    assert cm_obj.data_dict['level'] == pytest.approx(expected_level, abs=1e-6)

    # Assert that the time in data_dict is updated correctly
    assert cm_obj.data_dict['time'] == (frozen_time + timedelta(minutes=time_elapsed)).strftime('%Y-%m-%d %H:%M:%S')


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
    cm_obj.current_time = datetime.now()
    cm_obj.data_dict = {'level': 0.0, 'time': cm_obj.current_time.strftime('%Y-%m-%d %H:%M:%S')}

    # Set up self.current_item with required members
    cm_obj.current_item = {
        'level': mg_add,
        'when_to_process': cm_obj.current_time - timedelta(minutes=min_ago)
    }

    # Call the method
    cm_obj.decay_before_add()

    # Assert the expected behavior
    minutes_elapsed = min_ago
    expected_amount_left = mg_add * pow(0.5, (minutes_elapsed / cm_obj.half_life))
    assert cm_obj.mg_net_change == round(expected_amount_left, 1)


@pytest.mark.parametrize("mg, mins, expected_future_list_length", [
    (100, 180, 4),    # Normal case
    (0, 0, 4),        # Edge case: 0 mg and 0 mins
    (200, 0, 4),      # Edge case: mins_ago is 0
    (100, -30, 4),    # Edge case: negative mins_ago
])
def test_add_coffee(mocker, files_mocked, mg, mins, expected_future_list_length):
    open_mock, json_load_mock, json_dump_mock = files_mocked
    nmspc = Namespace(mg=mg, mins=mins, bev='coffee')
    cm_obj = CaffeineMonitor(open_mock, json_load_mock, json_load_mock, True, nmspc)
    cm_obj.current_time = datetime.now()

    cm_obj.add_coffee()

    assert len(cm_obj.future_list) == expected_future_list_length


@pytest.mark.parametrize("mg, mins, expected_future_list_length", [
    (200, 0, 3),      # Normal case
    (0, 0, 3),        # Edge case: 0 mg and 0 mins
    (300, 30, 3),     # Edge case: mins_ago is 30
    (100, -20, 3),    # Edge case: negative mins_ago
])
def test_add_soda(mocker, files_mocked, mg, mins, expected_future_list_length):
    open_mock, json_load_mock, json_dump_mock = files_mocked
    nmspc = Namespace(mg=mg, mins=mins, bev='soda')
    cm_obj = CaffeineMonitor(open_mock, json_load_mock, json_load_mock, True, nmspc)
    cm_obj.current_time = datetime.now()

    cm_obj.add_soda()

    assert len(cm_obj.future_list) == expected_future_list_length


@pytest.mark.parametrize("initial_level, mg, mins, expected_level", [
    (50.0, 100, 0, 150.0),  # Normal case
    (0.0, 0, 0, 0.0),  # Edge case: 0 initial level, 0 mg, and 0 mins
    (75.0, 200, 30, 275.0),  # Normal case with non-zero initial level and mins
    (100.0, -50, 0, 50.0),  # Case with negative mg (assuming add_caffeine() subtracts the absolute value)
])
@pytest.mark.parametrize("bev", ['coffee', 'soda', 'chocolate'])
def test_add_caffeine(files_mocked, initial_level, mg, mins, bev, expected_level):
    open_mock, json_load_mock, json_dump_mock = files_mocked
    nmspc = Namespace(mg=mg, mins=mins, bev=bev)
    cm_obj = CaffeineMonitor(open_mock, json_load_mock, json_load_mock, True, nmspc)

    # Set the initial level and time dynamically based on the test parameters
    cm_obj.data_dict = {"time": datetime.now().strftime('%Y-%m-%d %H:%M:%S'), "level": initial_level}
    cm_obj.mg_net_change = mg

    cm_obj.add_caffeine(mg)

    assert cm_obj.data_dict['level'] == expected_level


def test_update_time(files_mocked):
    nmspc = Namespace(mg=20, mins=20, bev='coffee')
    open_mock, json_load_mock, json_dump_mock = files_mocked
    cm_obj = CaffeineMonitor(open_mock, json_load_mock, json_load_mock, True, nmspc)
    cm_obj.read_file()  # loads cm.data_dict from file
    cm_obj.data_dict['time'] = (datetime.now() - timedelta(days=10)).strftime('%Y-%m-%d %H:%M:%S')
    freezer = freeze_time('2020-05-01 11:00:00')
    freezer.start()
    cm_obj.update_time()
    freezer.stop()
    assert cm_obj.data_dict['time'] == '2020-05-01 11:00:00'


def test_str(files_mocked):
    open_mock, json_load_mock, json_dump_mock = files_mocked
    nmspc = Namespace(mg=50, mins=50, bev='soda')
    cm_obj = CaffeineMonitor(open_mock, json_load_mock, json_load_mock, False, nmspc)
    cm_obj.data_dict['level'] = 48.0
    cm_obj.data_dict['time'] = datetime(2020, 4, 1, 12, 51).strftime('%Y-%m-%d %H:%M:%S')
    assert str(cm_obj) == 'Caffeine level is 48.0 mg at time 2020-04-01 12:51:00'


def test_read_log(files_mocked):
    nmspc = Namespace(mg=100, mins=0, bev='soda')
    open_mock, json_load_mock, json_dump_mock = files_mocked
    # open_mock below must be called; cm_obj.read_log iterates over list
    cm_obj = CaffeineMonitor(open_mock(), json_load_mock, json_load_mock, True, nmspc)
    cm_obj.read_log()
    assert cm_obj.log_contents[0] == 'Start of log file'
    assert cm_obj.log_contents[1] != cm_obj.log_contents[0]
    assert cm_obj.log_contents[2] == 1


@pytest.mark.parametrize("future_data, expected_future_list", [
    (
        [
            {"when_to_process": "2023-06-08 10:00:00", "time_entered": "2023-06-08 09:00:00", "level": 50.0},
            {"when_to_process": "2023-06-08 11:00:00", "time_entered": "2023-06-08 09:30:00", "level": 25.0}
        ],
        [
            {"when_to_process": datetime(2023, 6, 8, 11, 0, 0), "time_entered": datetime(2023, 6, 8, 9, 30, 0), "level": 25.0},
            {"when_to_process": datetime(2023, 6, 8, 10, 0, 0), "time_entered": datetime(2023, 6, 8, 9, 0, 0), "level": 50.0}
        ]
    ),
    (
        [],
        []
    ),
    (
        [
            {"when_to_process": "2023-06-08 10:00:00", "time_entered": "2023-06-08 09:00:00", "level": 50.0}
        ],
        [
            {"when_to_process": datetime(2023, 6, 8, 10, 0, 0), "time_entered": datetime(2023, 6, 8, 9, 0, 0), "level": 50.0}
        ]
    ),
    (
        [
            {"when_to_process": "2023-06-08 10:00:00", "time_entered": "2023-06-08 09:00:00", "level": 0.0}
        ],
        [
            {"when_to_process": datetime(2023, 6, 8, 10, 0, 0), "time_entered": datetime(2023, 6, 8, 9, 0, 0), "level": 0.0}
        ]
    ),
    (
        [
            {"when_to_process": "2023-06-08 09:00:00", "time_entered": "2023-06-08 08:00:00", "level": 30.0},
            {"when_to_process": "2023-06-08 10:00:00", "time_entered": "2023-06-08 09:00:00", "level": 50.0},
            {"when_to_process": "2023-06-08 11:00:00", "time_entered": "2023-06-08 09:30:00", "level": 25.0}
        ],
        [
            {"when_to_process": datetime(2023, 6, 8, 11, 0, 0), "time_entered": datetime(2023, 6, 8, 9, 30, 0), "level": 25.0},
            {"when_to_process": datetime(2023, 6, 8, 10, 0, 0), "time_entered": datetime(2023, 6, 8, 9, 0, 0), "level": 50.0},
            {"when_to_process": datetime(2023, 6, 8, 9, 0, 0), "time_entered": datetime(2023, 6, 8, 8, 0, 0), "level": 30.0}
        ]
    ),
    (
        [
            {"when_to_process": "2023-06-08 11:00:00", "time_entered": "2023-06-08 09:30:00", "level": 25.0},
            {"when_to_process": "2023-06-08 09:00:00", "time_entered": "2023-06-08 08:00:00", "level": 30.0},
            {"when_to_process": "2023-06-08 10:00:00", "time_entered": "2023-06-08 09:00:00", "level": 50.0}
        ],
        [
            {"when_to_process": datetime(2023, 6, 8, 11, 0, 0), "time_entered": datetime(2023, 6, 8, 9, 30, 0), "level": 25.0},
            {"when_to_process": datetime(2023, 6, 8, 10, 0, 0), "time_entered": datetime(2023, 6, 8, 9, 0, 0), "level": 50.0},
            {"when_to_process": datetime(2023, 6, 8, 9, 0, 0), "time_entered": datetime(2023, 6, 8, 8, 0, 0), "level": 30.0}
        ]
    ),
])
def test_read_future_file(files_mocked, future_data, expected_future_list):
    open_mock, json_load_mock, json_dump_mock = files_mocked

    # Configure the mock file to return the future data when json.load() is called
    json_load_mock.side_effect = [future_data]

    # Create an instance of CaffeineMonitor with the mocked files
    nmspc = Namespace(mg=100, mins=180, bev='coffee')
    cm_obj = CaffeineMonitor(open_mock, json_load_mock, json_load_mock, True, nmspc)

    # Call the read_future_file() method
    cm_obj.read_future_file()

    # Assert that the future_list attribute is set correctly
    assert cm_obj.future_list == expected_future_list


def create_namespace(mg, mins, bev):
    return Namespace(mg=mg, mins=mins, bev=bev)


@pytest.mark.parametrize(
    "mg_net_change, mins_ago, expected_level, expected_new_future_list",
    [
        # Test case 1: Item is in the past and should be processed, updating the level
        (50.0, 60, 100.0 + (50.0 * (0.5 ** (60/360))), []),

        # Test case 2: Item is in the future and should be added to new_future_list
        (25.0, -30, 100.0, [
            {
                "mins": 30,
                "level": 25.0,
            }
        ]),

        # Test case 3: Item is in the present and should be processed, updating the level
        (100.0, 0, 200.0, []),
    ],
)
def test_process_item_common_cases(files_mocked, mg_net_change, mins_ago, expected_level, expected_new_future_list, current_time_str):
    nmspc = Namespace(mg=mg_net_change, mins=mins_ago, bev='coffee')
    cm_obj = CaffeineMonitor(*files_mocked, True, nmspc)
    cm_obj.mg_net_change = mg_net_change
    cm_obj.mins_ago = mins_ago
    cm_obj.new_future_list = []
    cm_obj.data_dict = {'level': 100.0, 'time': current_time_str}
    cm_obj.current_item = {
        "level": cm_obj.mg_net_change,
        "when_to_process": datetime.strptime(current_time_str, '%Y-%m-%d %H:%M:%S') - timedelta(minutes=cm_obj.mins_ago),
        "time_entered": datetime.strptime(current_time_str, '%Y-%m-%d %H:%M:%S'),
    }
    cm_obj.process_item(cm_obj.mg_net_change)
    assert cm_obj.data_dict["level"] == pytest.approx(expected_level, rel=1e-3)

    # Convert datetime objects to string for comparison
    actual_new_future_list = [
        {
            "when_to_process": item["when_to_process"].strftime('%Y-%m-%d %H:%M:%S'),
            "time_entered": item["time_entered"].strftime('%Y-%m-%d %H:%M:%S'),
            "level": item["level"]
        }
        for item in cm_obj.new_future_list
    ]
    expected_new_future_list = [
        {
            "when_to_process": (datetime.strptime(current_time_str, '%Y-%m-%d %H:%M:%S') + timedelta(minutes=item["mins"])).strftime('%Y-%m-%d %H:%M:%S'),
            "time_entered": current_time_str,
            "level": item["level"]
        }
        for item in expected_new_future_list
    ]
    assert actual_new_future_list == expected_new_future_list


@pytest.mark.parametrize(
    "mg_net_change, mins_ago, expected_level, expected_new_future_list",
    [
        # Test case 1: Item with zero mg_net_change should not affect the level
        (0.0, 60, 100.0, []),

        # Test case 2: Item with 1 day (1440 minutes) ago should affect the level minimally due to decay
        (75.0, 1440, 100.0 + (75.0 * (0.5 ** (1440/360))), []),

        # Test case 3: Item with 1 day (-1440 minutes) in the future should be added to new_future_list
        (50.0, -1440, 100.0, [
            {
                "mins": 1440,
                "level": 50.0,
            }
        ]),
    ],
)
def test_process_item_edge_cases(files_mocked, mg_net_change, mins_ago, expected_level, expected_new_future_list, current_time_str):
    nmspc = Namespace(mg=mg_net_change, mins=mins_ago, bev='coffee')
    cm_obj = CaffeineMonitor(*files_mocked, True, nmspc)
    cm_obj.mg_net_change = mg_net_change
    cm_obj.mins_ago = mins_ago
    cm_obj.new_future_list = []
    cm_obj.data_dict = {'level': 100.0, 'time': current_time_str}
    cm_obj.current_item = {
        "level": cm_obj.mg_net_change,
        "when_to_process": datetime.strptime(current_time_str, '%Y-%m-%d %H:%M:%S') - timedelta(minutes=cm_obj.mins_ago),
        "time_entered": datetime.strptime(current_time_str, '%Y-%m-%d %H:%M:%S'),
    }
    cm_obj.process_item(cm_obj.mg_net_change)
    assert cm_obj.data_dict["level"] == pytest.approx(expected_level, rel=1e-3)

    # Convert datetime objects to string for comparison
    actual_new_future_list = [
        {
            "when_to_process": item["when_to_process"].strftime('%Y-%m-%d %H:%M:%S'),
            "time_entered": item["time_entered"].strftime('%Y-%m-%d %H:%M:%S'),
            "level": item["level"]
        }
        for item in cm_obj.new_future_list
    ]
    expected_new_future_list = [
        {
            "when_to_process": (datetime.strptime(current_time_str, '%Y-%m-%d %H:%M:%S') + timedelta(minutes=item["mins"])).strftime('%Y-%m-%d %H:%M:%S'),
            "time_entered": current_time_str,
            "level": item["level"]
        }
        for item in expected_new_future_list
    ]
    assert actual_new_future_list == expected_new_future_list


@pytest.mark.parametrize("future_list, expected_new_future_list", [
    # Normal case: process a single past item
    ([{"when_to_process": datetime(2023, 6, 8, 7, 0), "time_entered": datetime(2023, 6, 8, 6, 0), "level": 50.0}], []),

    # Normal case: process a single future item
    ([{"when_to_process": datetime(2023, 6, 8, 11, 0), "time_entered": datetime(2023, 6, 8, 8, 0), "level": 50.0}],
     [{"when_to_process": datetime(2023, 6, 8, 11, 0), "time_entered": datetime(2023, 6, 8, 8, 0), "level": 50.0}]),

    # Edge case: empty future list
    ([], []),
])
def test_process_future_list(mocker, files_mocked, future_list, expected_new_future_list):
    # Arrange
    nmspc = Namespace(mg=0, mins=0, bev='coffee')
    cm_obj = CaffeineMonitor(*files_mocked, True, nmspc)
    cm_obj.future_list = future_list
    cm_obj.new_future_list = []
    cm_obj.curr_time = datetime(2023, 6, 8, 9, 0)  # Set current_time one hour later than time_entered

    # Store the initial length of future_list
    initial_future_list_length = len(future_list)

    # Mock the process_item() method with a side effect
    def process_item_side_effect(mg_to_add_local):
        if cm_obj.when_to_process > cm_obj.curr_time:
            new_item = {"when_to_process": cm_obj.when_to_process, "time_entered": cm_obj.time_entered, "level": mg_to_add_local}
            cm_obj.new_future_list.append(new_item)

    mock_process_item = mocker.patch.object(cm_obj, 'process_item', side_effect=process_item_side_effect)

    # Act
    cm_obj.process_future_list()

    # Assert
    assert cm_obj.new_future_list == expected_new_future_list
    assert mock_process_item.call_count == initial_future_list_length


@pytest.mark.skip(reason="Not ready for this test yet")
@pytest.mark.parametrize("mg, walltime, initial_level, expected_level", [
    (100, "09:00", 50.0, 125.0),
    (50, "10:30", 75.0, 100.0),
    (200, "08:00", 100.0, 250.0),
])
def test_process_item_with_walltime(mocker, files_mocked, mg, walltime, initial_level, expected_level):
    # Arrange
    open_mock, json_load_mock, json_dump_mock = files_mocked
    current_datetime = datetime.now()
    args = [str(mg), "-w", walltime]
    parsed_args = parse_clas(args)
    cm_obj = CaffeineMonitor(open_mock, json_load_mock, json_load_mock, True, parsed_args)
    cm_obj.current_time = current_datetime
    cm_obj.data_dict = {"level": initial_level, "time": current_datetime.strftime('%Y-%m-%d %H:%M:%S')}

    # Set up the current_item for testing
    cm_obj.current_item = {
        "level": mg,
        "when_to_process": datetime.strptime(walltime, "%H:%M"),
        "time_entered": datetime.strptime(walltime, "%H:%M"),
    }

    # Act
    cm_obj.process_item(cm_obj.current_item["level"])

    # Assert
    assert cm_obj.data_dict["level"] == pytest.approx(expected_level, rel=1e-3)
