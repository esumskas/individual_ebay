from config import load_config, load_credentials
import logging
import os
import requests

cfg = load_config()

log = logging.getLogger(__name__)
# logging.basicConfig(level=logging.INFO)
console = logging.StreamHandler()
log.addHandler(console)


class Item:
    def __init__(self, crawler, file_handler):
        self.min_model_year = 0
        self.max_model_year = 0
        self.name = ""
        self.manufacturer = ""
        self.part_nr = ""
        self.analog_part_nr = []
        self.oe_part_nr = []
        self.oe_part_nr_shortened = []
        self.vehicles = []
        self.ean = ""
        self.supplier_price = 0
        self.stock = []
        self.details = []
        self.links = []
        self.img_links = []
        self.img_local_paths = []
        self.img_main_hosted_link = ""
        self.crawler = crawler
        self.crawled = False
        self.last = False
        self.file_handler = file_handler
        self.populate_item()

    def populate_item(self):
        """
        Get starting information about item (manufacturer and part number) from loaded csv file.
        :return:
        """
        row = self.file_handler.get_row()
        if row is not None:
            self.part_nr = row[1]
            self.manufacturer = row[4]
            self.ean = row[0]
            if float(row[6].replace(',', '.')) >= cfg['prices']['minimum_price_with_vat']:
                self.crawler.crawl_item_primary(self)
            else:
                log.info("[ITEM: " + self.part_nr + "]: Item price requirement is not met.")
        else:
            self.last = True

    def is_required_info_filled(self):
        if self.name != "" \
                and self.manufacturer != "" \
                and self.part_nr != "" \
                and self.oe_part_nr \
                and self.stock \
                and self.supplier_price != 0 \
                and self.img_links \
                and self.vehicles:
            return True
        else:
            return False

    def generate_unique_vehicles_list(self):
        """
        Simplifies and returns list of strings of unique vehicles

        :return: list of strings
        """
        simplified_list = []
        for row in self.vehicles:
            simplified_list.append(row[0] + " " + row[1].split(" ")[0])
        simplified_list = set(simplified_list)
        simplified_list = list(simplified_list)
        simplified_list.sort()
        return simplified_list

    def delete_image(self, img_path):
        log.info("[ITEM: " + self.part_nr + "]: Deleting regular picture PATH: [" + img_path + "]")
        os.remove(img_path)

    def upload_main_photo_to_host(self):
        log.info("[ITEM: " + self.part_nr + "]: Uploading picture PATH: [" + self.img_local_paths[0] + "] to site hosting and randomizing filename")
        user_agent_header = {'User-agent': cfg['user_agent']}
        url = 'https://domain.lt/upload_a739jdbgu2oj.php'
        img_link_start = 'https://domain.lt/uploads/'
        files = {'file': open(self.img_local_paths[0], 'rb')}
        r = requests.post(url, files=files, headers=user_agent_header)
        r.encoding = 'utf-8-sig'

        # print(r.text)
        if r.ok:
            img_link = img_link_start + r.text
            # print(img_link)
            self.img_main_hosted_link = img_link
        else:
            img_link = ""
            # print("nera")
            log.info(r.content)
