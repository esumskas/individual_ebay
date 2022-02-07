from Crawler import Crawler
from GFileHandler import GFileHandler
from EbayItem import EbayItem
from Item import Item
import logging
from config import load_config
# from sys import stderr, stdout
from datetime import datetime

cfg = load_config()
log = logging.getLogger(__name__)
# logging.basicConfig(level=logging.INFO)
#


# stderr.write = log.error
# stdout.write = log.info
console = logging.StreamHandler()
log.addHandler(console)

if __name__ == "__main__":

    format = "%(asctime)s %(name)s: %(message)s"
    logging.basicConfig(filename="logs/ebay_{:%Y%m%d_%H%M%S}.log".format(datetime.now()),
                        filemode="w",
                        format=format,
                        level=logging.INFO,
                        datefmt="%Y-%m-%d %H:%M:%S")
    if cfg['supplier'] == 'supplier':
        crawler = Crawler()
        file_handler = GFileHandler()
    while True:
        item = Item(crawler, file_handler)
        if item.last is True:
            break
        if item.is_required_info_filled():
            log.info("[ITEM: " + item.part_nr + "]: All info filled. Moving on")
            log.info("[ITEM: " + item.part_nr + "]: Creating eBay item object")
            ebay_item = EbayItem(item)
            if ebay_item.earnings < cfg['price_calculation']['minimum_earnings']:
                log.info("[ITEM: " + item.part_nr + "]: Item does not fulfill price requirements. Earnings: " +
                         (str(round(ebay_item.earnings, 2)) + " is less than defined minimum of " +
                          str(cfg['price_calculation']['minimum_earnings'])))
            else:
                ebay_item.fill_summary_html()
                ebay_item.fill_details_html()
                ebay_item.fill_vehicles_html()
                ebay_item.fill_description_html()
                ebay_item.fill_suggested_cat()
                crawler.download_images(item)
                item.upload_main_photo_to_host()
                ebay_item.upload_pictures_from_filesystem()
                ebay_item.list_item()
        else:
            log.info("[ITEM: " + item.part_nr + "]: Item does not have required info filled")
