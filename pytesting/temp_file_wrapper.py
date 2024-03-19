# file: pytesting/temp_file_wrapper.py

class TempFileWrapper:

    def __init__(self, tempfile):
        self.tempfile = tempfile

    def reset(self):
        self.tempfile.seek(0)
        self.tempfile.truncate()
