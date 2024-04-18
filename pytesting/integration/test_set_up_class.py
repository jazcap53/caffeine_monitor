# file: test_set_up_class.py
import pytest
from src.utils import set_up
import logging


class TestSetUp:
    @pytest.fixture(autouse=True)
    def setup(self, mocker):
        self.mocker = mocker
        self.mock_args = mocker.MagicMock()
        self.mock_parse_clas = mocker.patch('src.utils.parse_clas', return_value=self.mock_args)
        self.mock_config = {
            'prod': {'json_file': 'prod.json', 'json_file_future': 'prod_future.json', 'log_file': 'prod.log'},
            'devel': {'json_file': 'devel.json', 'json_file_future': 'devel_future.json', 'log_file': 'devel.log'},
            'pytesting': {'json_file': 'pytesting.json', 'json_file_future': 'pytesting_future.json', 'log_file': 'pytesting.log'}
        }
        self.mock_read_config_file = mocker.patch('src.utils.read_config_file', return_value=self.mock_config)
        self.mock_first_run = True
        self.mock_create_files = mocker.patch('src.utils.create_files', return_value=self.mock_first_run)
        self.mock_check_cla_match_env = mocker.patch('src.utils.check_cla_match_env')
        self.mock_logging_basicConfig = mocker.patch('logging.basicConfig')

    @pytest.mark.parametrize('caff_env', ['prod', 'devel', 'pytesting'])
    def test_set_up_valid_env(self, caff_env):
        # Arrange
        expected_args = ['script.py']
        if caff_env == 'devel':
            expected_args = ['script.py', '-d']
        elif caff_env == 'pytesting':
            expected_args = ['script.py', '-q']
        self.mocker.patch.dict('os.environ', {'CAFF_ENV': caff_env})
        self.mocker.patch('sys.argv', expected_args)

        # Act
        log_filename, json_filename, json_future_filename, first_run, args = set_up()

        # Assert
        expected_log_filename = self.mock_config[caff_env]['log_file']
        expected_json_filename = self.mock_config[caff_env]['json_file']
        expected_json_future_filename = self.mock_config[caff_env]['json_file_future']

        self.mock_parse_clas.assert_called_once_with(expected_args[1:])
        self.mock_read_config_file.assert_called_once_with('src/caffeine.ini')
        self.mock_check_cla_match_env.assert_called_once_with(caff_env, self.mock_args)
        self.mock_create_files.assert_called_once_with(expected_log_filename, expected_json_filename, expected_json_future_filename)
        self.mock_logging_basicConfig.assert_called_once_with(filename=expected_log_filename, level=logging.INFO,
                                                              format='%(levelname)s: %(message)s')
        assert log_filename == expected_log_filename
        assert json_filename == expected_json_filename
        assert json_future_filename == expected_json_future_filename
        assert first_run == self.mock_first_run
        assert args == self.mock_args

    @pytest.mark.parametrize('caff_env', ['nonsense', None, ''])
    def test_set_up_invalid_env(self, caff_env):
        # Arrange
        self.mocker.patch.dict('os.environ', clear=True)

        # Act and Assert
        with pytest.raises(SystemExit):
            set_up()
