import io
from caffeine_monitor import CoffeeMonitor


def test_create_monitor_from_text_io_string(capsys):
    wrap = io.StringIO('bongo.txt')
    print(f'Type of \"wrap\" is {type(wrap)}')
    out, err = capsys.readouterr()
    cm = CoffeeMonitor(wrap)
    # cm.read_file()
    wrap.close()
    assert out == "Type of \"wrap\" is <class '_io.StringIO'>\n"
    assert isinstance(cm.iofile, io.StringIO)
    assert cm.old_time is cm.level is cm.curr_time is None
    assert cm.data_dict == {}
    assert cm.mg_to_add == 0
    assert cm.mins_ago == 0
