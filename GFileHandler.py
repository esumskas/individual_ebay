import csv
from config import load_config, load_credentials
import logging
from sys import exit

cfg = load_config()

log = logging.getLogger(__name__)
# logging.basicConfig(level=logging.INFO)
console = logging.StreamHandler()
log.addHandler(console)


class GFileHandler:
    def __init__(self):
        self.current_row = 0
        self.file = ""
        self.file_csv = ""
        self.load_file()

    def load_file(self):
        log.info('Loading file')
        try:
            self.file = open(cfg['items_file_name'], 'r', encoding="utf8")
            # self.file_csv = csv.reader(self.file, delimiter="\t")
            self.file_csv = list(csv.reader(self.file, delimiter='\t'))
            self.file.close()
        except IOError:
            log.error('IO Error on items file read. Exitting')
            exit()

    def get_row(self):
        if self.current_row < len(self.file_csv) - 1:
            self.current_row += 1
            log.info('Getting row nr. ' + str(self.current_row))
            return self.file_csv[self.current_row]
        else:
            log.info('File end reached')
            return None


if __name__ == '__main__':
    FileHandler = GFileHandler()
    FileHandler.get_row()
