from bs4 import BeautifulSoup
from config import load_config, load_credentials
import logging
from HTTP import HTTP
import re
import random

cfg = load_config()
creds = load_credentials()

log = logging.getLogger(__name__)
# logging.basicConfig(level=logging.INFO)
console = logging.StreamHandler()
log.addHandler(console)


class Crawler:
    def __init__(self):
        self.HTTP = HTTP()
        self.login()
        self.raw_object = ""

    def login(self):
        log.info("Logging in to domain web catalog")
        r = self.HTTP.request("GET", 'http://domain.lt/loginform-domain.aspx')
        soup = BeautifulSoup(r.content, features="lxml")
        data = {
            'btnLogin': 'Sign In',
            'tbLoginName': creds['domain_web']['username'],
            'tbPassword': creds['domain_web']['password'],
            'ctl05': 'ctl06|btnLogin',
            '__EVENTTARGET': "",
            '__EVENTARGUMENT': "",
            '__ASYNCPOST': "true",
            '__LASTFOCUS': ""
        }
        data['__VIEWSTATE'] = soup.find(id="__VIEWSTATE")['value']
        data['__VIEWSTATEGENERATOR'] = soup.find(id="__VIEWSTATEGENERATOR")['value']
        data['__EVENTVALIDATION'] = soup.find(id="__EVENTVALIDATION")['value']
        r = self.HTTP.request("POST", 'http://domain.lt/loginform-domain.aspx', data=data)
        return r.status_code

    def search(self, item):
        """
        Searches for item in Domain Web Catalog.

        :param item:
        :return:
        """
        search_string = item.part_nr
        log.info("[ITEM: " + item.part_nr + "]: Starting search on string: " + search_string)
        r = self.HTTP.request('GET', 'http://domain.lt/partscatalogue/searchresult.aspx?search=' +
                              search_string)
        soup = BeautifulSoup(r.content, features="lxml")
        if soup.find(id="ctl00_pagecontext_lbCountText") is not None:
            result_count = int(soup.find(id="ctl00_pagecontext_lbCountText").get_text().split(" ")[1])
            log.info("[ITEM: " + item.part_nr + "]: Search returned " + str(result_count) + " results.")
            for link in soup.findAll('div', {'class': 'partscontrol-box'}):
                item.links.append('http://catalogue.domain-orders.lt' +
                                  link.find('a', {'class': 'partscontrol-box-detail-link'})['href'])
        elif soup.find(id="ctl00_panelError") is not None:
            log.info("Search returned 0 results.")
        else:
            log.error("Error")

    def fill_name(self, item):
        item.name = self.raw_object.find('div', {'class': 'ofptecdoc_genartnamerow'}).\
            find('div', {'class': 'ofptecdoc_genartname'}).get_text()

    def fill_stock(self, item):
        """
        Fills item.stock property with list of stocks
        0 = stocks code
        1 = item stock

        :param item:
        :return:
        """
        qua_cont = self.raw_object.findAll('div', {'class': 'qua_cont'})
        for quantity in qua_cont:
            # item.stock[quantity.find('span', {'class': 'code'}).get_text()] = \
            #     int(quantity.find('div', {'class': 'qua_no'}).get_text().replace(">", ""))
            item.stock.append([quantity.find('span', {'class': 'code'}).get_text(),
                               int(quantity.find('div', {'class': 'qua_no'}).get_text().replace(">", ""))])
        # print(qua_cont)
        # print(item.stock)

    def fill_details(self, item):
        """
        Fills item.details property with list of details
        0 = detail name
        1 = detail value
        :param item:
        :return:
        """
        description = self.raw_object.find(itemprop="description")
        if description is not None:
            description = description.find_all('div', {'class': 'infocontext'})
            for val in description:
                key = val.find('span', {'class': 'partiname'})
                val1 = val.find('span', {'class': 'partival'})
                if key is not None and val1 is not None:
                    # item.details[key.get_text()] = val1.get_text()
                    item.details.append([key.get_text(), val1.get_text()])
        else:
            log.info("[ITEM: " + item.part_nr + "]: Item does not have description table")

            # print(item.details)

    def fill_analog_part_numbers(self, item):
        """
        Fills item.analog_part_nr property with list of part numbers
        0 = manufacturer
        1 = analog part nr

        :param item:
        :return:
        """
        a = self.raw_object.find('a', string="substitutes")['href']
        r = self.HTTP.request('GET', 'http://domain.lt' + a)
        soup = BeautifulSoup(r.content, features="lxml")
        rows = soup.find_all('tr', {'class': re.compile('dgrid(.*)item')})
        # rows += soup.find_all('tr', {'class': 'dgridaltitem'})
        for row in rows:
            producer = row.find('td', {'class': 'producer'})
            part_nr = row.find('td', {'class': 'additional_data'})
            if producer is not None and part_nr is not None:
                # item.analog_part_nr[producer.get_text()] = part_nr.get_text().rsplit(" ", 1)[0]
                item.analog_part_nr.append([producer.get_text().replace("&", " "), part_nr.get_text().rsplit(" ", 1)[0]])
                # item.analog_part_nr.sort()
        # print(item.analog_part_nr)

    def fill_oe_part_numbers(self, item):
        """
        Fills item.oe_part_nr property with list of OE part numbers
        0 = manufacturer
        1 = oe part number

        :param item:
        :return:
        """
        a = self.raw_object.find('a', string="code OE")['href']
        r = self.HTTP.request('GET', 'http://domain.lt' + a)
        soup = BeautifulSoup(r.content, features="lxml")
        rows = soup.find_all('tr', {'class': re.compile("partoecodescontrol-(.*)item")})
        # rows += soup.find_all('tr', {'class': 'partoecodescontrol-altitem'})

        for row in rows:
            item.oe_part_nr.append(row.find('td', {'class': 'oename'}).get_text().replace("&", "") + " " +
                                   row.find('td', {'class': 'oecode'}).get_text())

        if len(item.oe_part_nr) > 30:
            while len(item.oe_part_nr_shortened) < 30:
                row_to_add = random.choice(item.oe_part_nr)
                if row_to_add not in item.oe_part_nr_shortened:
                    item.oe_part_nr_shortened.append(row_to_add)

        if len(item.oe_part_nr) == 0:
            log.info("[ITEM: " + item.part_nr + "]: Item does not have oe numbers filled")
        # print(len(item.oe_part_nr), len(item.oe_part_nr_shortened))
            # item.oe_part_nr.sort()
        # print(item.oe_part_nr)

    def fill_vehicles(self, item):
        """
        Fills item.vehicles property with list of vehicles which part is suitable.
        0 = Mark
        1 = Model
        2 = engine Type
        3 = engine code
        4 = engine Power [kW]
        5 = engine Power [HP]
        6 = engine Capacity [cm3]
        7 = years of production

        Also fills item.min_model_year and item.max_model_year properties
        :param item:
        :return:
        """
        a = self.raw_object.find('a', string="The vehicles")['href']
        if a is not None:
            # print(a)
            r = self.HTTP.request('GET', 'http://domain.lt' + a)
            soup = BeautifulSoup(r.content, features="lxml")
            rows = soup.find_all('tr', {'class': re.compile("dgrid(.*)item")})
            # print(rows)
            if rows:
                # rows += soup.find_all('tr', {'class': 'dgridaltitem'})
                unformatted_years_list = []
                for row in rows:
                    rows1 = row.find_all('td')
                    item.vehicles.append([rows1[0].get_text(), rows1[1].get_text(), rows1[2].get_text(),
                                          rows1[3].get_text(), rows1[4].get_text(), rows1[5].get_text(),
                                          rows1[6].get_text(), rows1[7].get_text()])
                    unformatted_years_list.append(rows1[7].get_text())

                self.fill_min_max_model_year(item, unformatted_years_list)
        else:
            log.info("[ITEM: " + item.part_nr + "]: Item does not have The vehicles tab")
        if not item.vehicles:
            log.info("[ITEM: " + item.part_nr + "]: Item does not have vehicles filled")
        # print(item.vehicles)
        # print(rows)

    @staticmethod
    def fill_min_max_model_year(item, unformatted_years_list):
        formatted_list = []
        for row in unformatted_years_list:
            first = row.split(" - ")[0].split(".")[0]
            second = row.split(" - ")[1].split(".")[0]
            if first == "" and second == "":
                continue
            if second == "":
                second = 2020
            formatted_list.append([int(first), int(second)])
        item.min_model_year = min(map(min, formatted_list))
        item.max_model_year = max(map(max, formatted_list))

    def fill_price(self, item):
        item.supplier_price = float(self.raw_object.find(itemprop="price")['content'])
        if item.supplier_price and item.supplier_price != 0:
            pass
            #TODO: Padaryti kainos apskaiciavima
        # print(item.supplier_price)

    def fill_images_links(self, item):
        a = self.raw_object.find(id="ctl00_pagecontext_articleimagecontrol1_PanelThumbs")
        b = self.raw_object.find(id="ctl00_pagecontext_articleimagecontrol1_PanelLargeImg")
        if a is not None:
            a = a.find_all('a')
            for row in a:
                if "&" in row['href'] and "size=" in row['href'].rsplit("&", 1)[1]:
                    item.img_links.append("http://domain.lt" + row['href'].rsplit("&", 1)[0])
                else:
                    item.img_links.append("http://domain.lt" + row['href'])
        elif b is not None:
            b = b.find_all('img')
            if b:
                for row in b:
                    if "&" in row['src'] and "size=" in row['src'].rsplit("&", 1)[1]:
                        item.img_links.append("http://domain.lt" + row['src'].rsplit("&", 1)[0])
                    else:
                        item.img_links.append("http://domain.lt" + row['src'])
        else:
            log.info("[ITEM: " + item.part_nr + "]: Item does not have pictures")
        # print(item.img_links)

    def download_images(self, item):
        for i in range(0, len(item.img_links)):
            j = i + 1
            log.info("[ITEM: " + item.part_nr + "]: Downloading picture nr.: " + str(j))
            img_path = 'img/' + item.part_nr.replace(" ", "") + "-" + str(j) + '.jpg'
            with open(img_path, 'wb') as handle:
                response = self.HTTP.request("GET", item.img_links[i])

                if not response.ok:
                    print(response)

                for block in response.iter_content(1024):
                    if not block:
                        break

                    handle.write(block)
            item.img_local_paths.append(img_path)

    def crawl_item_primary(self, item):
        self.search(item)
        if item.links:
            r = self.HTTP.request('GET', item.links[0])
            self.raw_object = BeautifulSoup(r.content, features="lxml")
            self.fill_name(item)
            self.fill_stock(item)
            self.fill_details(item)
            self.fill_analog_part_numbers(item)
            self.fill_oe_part_numbers(item)
            self.fill_vehicles(item)
            self.fill_price(item)
            self.fill_images_links(item)
            # self.download_images(item)
            # item.upload_main_photo_to_host()
            # print(item.ean, item.name, item.manufacturer)
        else:
            log.info("[ITEM: " + item.part_nr + "]: Item does not have links")
