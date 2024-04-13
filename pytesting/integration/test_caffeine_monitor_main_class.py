# file: test_caffeine_monitor_main_class.py

import pytest
from datetime import datetime, timedelta
from argparse import Namespace
from src.caffeine_monitor import CaffeineMonitor


class TestCaffeineMonitorMain:
    @pytest.fixture(autouse=True)
    def setup(self, mocker, files_mocked):
        self.mocker = mocker
        self.open_mock, self.json_load_mock, self.json_dump_mock = files_mocked

    @pytest.mark.parametrize("data_dict", [
        {'time': datetime.now().strftime('%Y-%m-%d_%H:%M'), 'level': 0.0},
        {'time': (datetime.now() - timedelta(hours=2)).strftime('%Y-%m-%d_%H:%M'), 'level': 50.0},
        {'time': (datetime.now() + timedelta(hours=1)).strftime('%Y-%m-%d_%H:%M'), 'level': 75.0},
    ])
    def test_main_with_different_data_dict(self, data_dict):
        nmspc = Namespace(mg=100, mins=0, bev='coffee')
        cm_obj = CaffeineMonitor(self.open_mock, self.json_load_mock, self.json_load_mock, True, nmspc)
        self.mocker.patch.object(cm_obj, 'read_file', return_value=None)
        cm_obj.data_dict = data_dict  # Populate data_dict directly
        self.mock_main_sub_methods(cm_obj)
        cm_obj.main()
        self.assert_main_sub_methods_called(cm_obj, first_run=True)

    @pytest.mark.parametrize("mg, mins, bev, first_run", [
        (100, 0, 'coffee', True),
        (50, 30, 'soda', False),
        (0, 0, 'chocolate', True),
        (200, -60, 'coffee', False),
    ])
    def test_main_with_different_params(self, mg, mins, bev, first_run):
        nmspc = Namespace(mg=mg, mins=mins, bev=bev)
        cm_obj = CaffeineMonitor(self.open_mock, self.json_load_mock, self.json_load_mock, first_run, nmspc)
        self.mocker.patch.object(cm_obj, 'read_file', return_value=None)
        cm_obj.data_dict = {'time': datetime.now().strftime('%Y-%m-%d_%H:%M'), 'level': 0.0}  # Populate data_dict
        self.mock_main_sub_methods(cm_obj)
        cm_obj.main()
        self.assert_main_sub_methods_called(cm_obj, first_run=first_run, bev=bev)

    def mock_main_sub_methods(self, cm_obj):
        self.read_log_mock = self.mocker.patch.object(cm_obj, 'read_log')
        self.read_file_mock = self.mocker.patch.object(cm_obj, 'read_file')
        self.read_future_file_mock = self.mocker.patch.object(cm_obj, 'read_future_file')
        self.decay_prev_level_mock = self.mocker.patch.object(cm_obj, 'decay_prev_level')
        self.add_coffee_mock = self.mocker.patch.object(cm_obj, 'add_coffee')
        self.add_soda_mock = self.mocker.patch.object(cm_obj, 'add_soda')
        self.process_future_list_mock = self.mocker.patch.object(cm_obj, 'process_future_list')
        self.update_time_mock = self.mocker.patch.object(cm_obj, 'update_time')
        self.write_future_file_mock = self.mocker.patch.object(cm_obj, 'write_future_file')
        self.write_file_mock = self.mocker.patch.object(cm_obj, 'write_file')

    def assert_main_sub_methods_called(self, cm_obj, first_run, bev=None):
        self.read_log_mock.assert_called_once()
        self.read_file_mock.assert_called_once()
        self.read_future_file_mock.assert_called_once()
        if not first_run:
            self.decay_prev_level_mock.assert_called_once()
        else:
            self.decay_prev_level_mock.assert_not_called()
        if cm_obj.beverage == 'coffee':
            self.add_coffee_mock.assert_called_once()
            self.add_soda_mock.assert_not_called()
        elif cm_obj.beverage == 'soda':
            self.add_soda_mock.assert_called_once()
            self.add_coffee_mock.assert_not_called()
        else:
            self.add_coffee_mock.assert_not_called()
            self.add_soda_mock.assert_not_called()
