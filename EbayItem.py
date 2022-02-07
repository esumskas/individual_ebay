import random
import logging
from config import load_config, load_credentials
from ebaysdk.trading import Connection as Trading
from ebaysdk.finding import Connection as Finding
from ebaysdk.shopping import Connection as Shopping
import ebaysdk.exception
from os import sys
from time import sleep
import requests.exceptions

log = logging.getLogger(__name__)
# logging.basicConfig(level=logging.INFO)
console = logging.StreamHandler()
log.addHandler(console)
cfg = load_config()
creds = load_credentials()


class EbayItem:
    def __init__(self, item):
        self.item = item
        self.title = ""
        self.description_html = ""
        self.oe_numbers_html = ""
        self.summary_html = ""
        self.details_html = ""
        self.vehicles_html = ""
        self.hosted_img_url = self.item.img_main_hosted_link
        self.uploaded_img_urls = []
        self.similar_items = []
        self.similar_item_lowest_price = 0
        self.prime_cost = 0
        self.selling_price = 0
        self.earnings = 0
        self.earnings_percentage = 0
        self.minimum_selling_price = 0
        self.minimum_selling_price = 0
        self.suggested_cat = ""
        self.fill_primary_info()
        # self.fill_summary_html()
        # self.fill_details_html()
        # self.fill_vehicles_html()
        # self.fill_description_html()
        # self.upload_pictures_from_filesystem()
        # self.fill_suggested_cat()

    def fill_title(self):
        vehicles_in_title_list = []
        unique_vehicles_list = self.item.generate_unique_vehicles_list()
        if len(unique_vehicles_list) < cfg['vehicles_shown_in_title']:
            vehicles_range = len(unique_vehicles_list)
        else:
            vehicles_range = cfg['vehicles_shown_in_title']
        for i in range(0, vehicles_range):
            candidate = random.choice(unique_vehicles_list)
            while candidate in vehicles_in_title_list:
                candidate = random.choice(unique_vehicles_list)
            vehicles_in_title_list.append(candidate)
        vehicles_in_title_list.sort()
        retry_count = 0
        generated = False
        while (len(self.title) > 80 and len(vehicles_in_title_list) >= retry_count) or not generated:
            vehicles = ""
            for i in range(0, len(vehicles_in_title_list) - retry_count):
                if i == 0:
                    vehicles += vehicles_in_title_list[i] + " "
                elif vehicles_in_title_list[i].split(" ")[0] == vehicles_in_title_list[i - 1].split(" ")[0]:
                    vehicles += vehicles_in_title_list[i].split(" ")[1] + " "
                else:
                    vehicles += vehicles_in_title_list[i] + " "
            # random_oe_nr = ""
            if len(self.item.oe_part_nr) > 1:
                random_oe_nr = str(self.item.oe_part_nr[random.randrange(0, len(self.item.oe_part_nr)-1)].split(" ", 1)[1].replace(" ", "").replace(".", ""))
            else:
                random_oe_nr = self.item.oe_part_nr[0]
            self.title = "NEW " + \
                         self.item.manufacturer + \
                         " " + self.item.name.upper() + \
                         " FITS " + \
                         vehicles + \
                         random_oe_nr
            retry_count += 1
            generated = True
        print(self.title)

    # def fill_oe_numbers_html(self):
    #     self.oe_numbers_html = """<table align="center" style="border-spacing: 0px; width: 70%;">
    #     <tr>"""
    #     for i in range(0, len(self.item.oe_part_nr)):
    #         self.oe_numbers_html += """<tr>
    #                                     <td>""" + self.item.oe_part_nr[i][0] + """</td>
    #                                     <td>""" + self.item.oe_part_nr[i][1] + """</td>
    #                                     """
    #     self.oe_numbers_html += """</table>"""

    def fill_summary_html(self):
        oe_part_numbers = []
        for row in self.item.oe_part_nr:
            oe_part_numbers.append(row)
        unique_oe_numbers = list(set(oe_part_numbers))
        # print(unique_oe_numbers)
        car_manufacturers = []
        car_models = []
        for row in self.item.vehicles:
            car_manufacturers.append(row[0])
            car_models.append(row[1].split(" (")[0])
        unique_car_manufacturers = list(set(car_manufacturers))
        unique_car_models = list(set(car_models))
        self.summary_html = """
                        <tr><td>Years</td><td>""" + str(self.item.min_model_year) + " - " \
                       + str(self.item.max_model_year) + """</td></tr>
                        <tr><td>Brands</td><td>""" \
                       + str(unique_car_manufacturers).replace("'", "").replace(",", "").strip("[]") \
                       + """</td></tr>
                       <tr><td>Models</td><td>""" \
                       + str(unique_car_models).replace("'", "").replace(",", "").strip("[]") \
                       + """</td></tr>
                       <tr><td>OE Numbers</td><td>""" \
                       + str(unique_oe_numbers).replace("'", "").replace(",", "").strip("[]") \
                       + """</td></tr>
                       """

    def fill_details_html(self):
        self.details_html = """
                    <div class="col s12 m6">
                        <div class="card-panel">
                            <p class="header" style="color: #ce212b; font-size: 20px">Item specifications</p>
                            <table class="striped bordered table-sm">
                    """
        for i in range(0, len(self.item.details)):
            self.details_html += """<tr>
                                        <td>""" + self.item.details[i][0] + """</td>
                                        <td>""" + self.item.details[i][1] + """</td>
                                        """
        self.details_html += """
                                      </table>
                                    </div>
                                </div>
                                  """

    def fill_vehicles_html(self):
        self.vehicles_html = """
                        <tr>
                            <th>Brand</th>
                            <th>Model</th>
                            <th>Engine</th>
                            <th>Engine codes</th>
                            <th>Power [kW]</th>
                            <th>Power [HP]</th>
                            <th>Engine capacity [cm3]</th>
                            <th>Years</th>
                            """
        # app_table = ""

        for i in range(0, len(self.item.vehicles)):
            self.vehicles_html += """
                                       <tr>
                                       <td>""" + self.item.vehicles[i][0] + """</td>
                                       <td>""" + self.item.vehicles[i][1] + """</td>
                                       <td>""" + self.item.vehicles[i][2] + """</td>
                                       <td>""" + self.item.vehicles[i][3] + """</td>
                                       <td>""" + self.item.vehicles[i][4] + """</td>
                                       <td>""" + self.item.vehicles[i][5] + """</td>
                                       <td>""" + self.item.vehicles[i][6] + """</td>
                                       <td>""" + self.item.vehicles[i][7] + """</td>
                                       </tr>"""
        # app_table = app_table + """</table>"""

    def upload_pictures_from_filesystem(self):
        for i in range(0, len(self.item.img_local_paths)):
            log.info("[ITEM: " + self.item.part_nr + "]: Uploading picture PATH: [" +
                     self.item.img_local_paths[i] + "] to eBay")
            try:
                # api = Trading(config_file="ebay.yml", domain="api.ebay.com")
                if cfg['work_mode'] == "sandbox":
                    api = Trading(config_file="credentials.yml", domain="api.sandbox.ebay.com")
                elif cfg['work_mode'] == "production":
                    api = Trading(config_file="credentials.yml", domain="api.ebay.com")
                else:
                    print("CANNOT DETERMINE WHICH WORK MODE TO USE. EXITTING")
                    sys.exit()
                # pass in an open file
                # the Requests module will close the file
                files = {'file': ('EbayImage', open(self.item.img_local_paths[i], 'rb'))}

                pictureData = {
                    "WarningLevel": "High",
                    "PictureName": self.item.part_nr.rsplit(" ", 1)[0].replace(" ", "")
                }
                api.execute('UploadSiteHostedPictures', pictureData, files=files)
                full_url = (api.response_dict().get("SiteHostedPictureDetails").get("FullURL"))

                self.uploaded_img_urls.append(full_url)
                self.item.delete_image(self.item.img_local_paths[i])

            except ConnectionError as e:
                print(e)
                # print(e.response.dict())

    def find_similar_items(self):
        api = Finding(config_file='credentials.yml', siteid="EBAY-GB")
        api1 = Shopping(config_file='credentials.yml', siteid="3")
        query = self.item.part_nr.rsplit(" ", 1)[0] + " " + self.item.manufacturer
        # query = self.item.part_nr.rsplit(" ", 1)[0] + " " + self.item.manufacturer + " " + self.item.name
        request = {
            # 'keywords': '103735 TOPRAN',
            'keywords': query,
            'buyerCountryCode': 'LT',
            # 'aspectFilter': [
            #     {'aspectName': 'Brand'},
            #     {'aspectValueName': self.item.manufacturer}
            # ],
            'itemFilter': [
                {'name': 'Condition', 'value': 'New'},
                {'name': 'LocatedIn', 'value': ['lt', 'lv', 'gb', 'pl']},
                # {'name': 'Brand', 'value': str(self.item.manufacturer).lower()}
            ],
            'sortOrder': 'BestMatch'
            # 'sortOrder': 'PricePlusShippingLowest'

        }
        response = {}
        err = 0
        try:
            response = api.execute('findItemsByKeywords', request)
        except requests.exceptions.ConnectionError as error:
            log.error(error)
            if "IP limit exceeded" in str(error):
                log.error("IP limit exceeded. Exitting")
                sys.exit()
            log.error("Something went wrong in findItemsByKeywords request. Retrying one more time after 4 seconds")
            # response['paginationOutput']['totalEntries'] = "0"
            err = 1
        if err == 1:
            try:
                sleep(4)
                response = api.execute('findItemsByKeywords', request)
            except requests.exceptions.ConnectionError as error:
                log.error(error)
                if "IP limit exceeded" in str(error):
                    log.error("IP limit exceeded. Exitting")
                    sys.exit()
                log.error("Something went wrong in findItemsByKeywords request. Skipping")
                # response['paginationOutput']['totalEntries'] = "0"
        j = 0
        # print(response.dict())
        if response and not response.dict()['paginationOutput']['totalEntries'] == "0":
            categories = []
            for item in response.reply.searchResult.item:
                if j > 7:
                    break
                try:
                    # print(item.itemId)
                    sleep(0.5)
                    r = api1.execute('GetSingleItem',
                                     {'IncludeSelector': 'ItemSpecifics, ShippingCosts',
                                      'ItemID': item.itemId})
                except ebaysdk.exception.ConnectionError as error:
                    log.error(error)
                    if "IP limit exceeded" in str(error):
                        log.error("IP limit exceeded. Exitting")
                        sys.exit()
                    log.error("Something went wrong in GetSingleItem request. Continuing without retrying")
                    j += 1
                    continue
                # print(r.dict())
                try:
                    values_dict = (r.dict()['Item']['ItemSpecifics']['NameValueList'])
                except:
                    continue
                if type(values_dict) is dict:
                    if values_dict['Name'] == "Brand":
                        if str(values_dict['Value']).lower() == self.item.manufacturer.lower():
                            if "ShippingCostSummary" in r.dict()['Item']:
                                try:
                                    self.similar_items.append([
                                        r.dict()['Item']['ItemID'],
                                        r.dict()['Item']['Title'],
                                        r.dict()['Item']['ConvertedCurrentPrice']['value'],
                                        r.dict()['Item']['ShippingCostSummary']['ListedShippingServiceCost']['value'],
                                        float(r.dict()['Item']['ConvertedCurrentPrice']['value']) +
                                        float(r.dict()['Item']['ShippingCostSummary']['ListedShippingServiceCost'][
                                                  'value']),
                                        r.dict()['Item']['PrimaryCategoryID'],
                                        values_dict['Value']
                                    ])
                                except KeyError:
                                    continue
                else:
                    for dict_item in values_dict:
                        if dict_item['Name'] == "Brand":
                            if str(dict_item['Value']).lower() == self.item.manufacturer.lower():
                                if "ShippingCostSummary" in r.dict()['Item']:
                                    try:
                                        self.similar_items.append([
                                            r.dict()['Item']['ItemID'],
                                            r.dict()['Item']['Title'],
                                            r.dict()['Item']['ConvertedCurrentPrice']['value'],
                                            r.dict()['Item']['ShippingCostSummary']['ListedShippingServiceCost']['value'],
                                            float(r.dict()['Item']['ConvertedCurrentPrice']['value']) +
                                            float(r.dict()['Item']['ShippingCostSummary']['ListedShippingServiceCost']['value']),
                                            r.dict()['Item']['PrimaryCategoryID'],
                                            dict_item['Value']
                                        ])
                                    except KeyError:
                                        continue
                            break
                j += 1
            for i in range(0, len(self.similar_items)):
                try:
                    sleep(0.5)
                    r = api1.execute('GetShippingCosts', {'ItemID': self.similar_items[i][0], 'DestinationCountryCode': 'LT'})
                except ebaysdk.exception.ConnectionError:
                    continue
                try:
                    self.similar_items[i][3] = r.dict()['ShippingCostSummary']['ListedShippingServiceCost']['value']
                except KeyError:
                    continue
                # add selling price + shipping cost to list index 4
                self.similar_items[i][4] = float(self.similar_items[i][2]) + float(self.similar_items[i][3])
            print(self.similar_items)

    def fill_suggested_cat(self):
        if len(self.similar_items) > 0:
            cats = []
            for item in self.similar_items:
                cats.append(item[5])
            self.suggested_cat = max(set(cats), key=cats.count)
        else:
            log.info("[ITEM: " + self.item.part_nr + "]: Cannot fill suggested cat because there are no similar items")

    def fill_similar_item_lowest_price(self):
        if len(self.similar_items) > 0:
            prices = []
            for item in self.similar_items:
                prices.append(float(item[4]))
            self.similar_item_lowest_price = float(min(prices))
        else:
            log.info("[ITEM: " + self.item.part_nr + "]: Cannot fill lowest price because there are no similar items")

    def calculate_selling_price(self):
        postage_expenses = float(cfg['price_calculation']['post_expenses'])
        other_expenses = int(cfg['price_calculation']['other_expenses_proc'])
        difference_from_lowest_price = float(cfg['price_calculation']['difference_from_lowest_price'])

        self.prime_cost = (self.item.supplier_price + postage_expenses) * ((other_expenses / 100) + 1)
        self.selling_price = self.similar_item_lowest_price - difference_from_lowest_price
        self.earnings = self.selling_price - self.item.supplier_price - postage_expenses - (self.selling_price * (other_expenses / 100))
        self.earnings_percentage = self.selling_price * 100 / self.earnings

        log.info("[ITEM: " + self.item.part_nr + "]: Prime cost: " + str(round(self.prime_cost, 2)))
        log.info("[ITEM: " + self.item.part_nr + "]: Calculated selling price: " + str(round(self.selling_price, 2)))
        log.info("[ITEM: " + self.item.part_nr + "]: Earnings: " + str(round(self.earnings, 2)))
        log.info("[ITEM: " + self.item.part_nr + "]: Earnings percentage: " + str(round(self.earnings_percentage, 2)))

    def fill_primary_info(self):
        self.fill_title()
        self.find_similar_items()
        self.fill_similar_item_lowest_price()
        self.calculate_selling_price()

    def list_item(self):
        log.info("[ITEM: " + self.item.part_nr + "]: Trying to list item")
        if cfg['work_mode'] == "sandbox":
            api = Trading(config_file="credentials.yml", domain="api.sandbox.ebay.com")
            pp_mail_address = cfg['pp_mail_address']['sandbox']
        elif cfg['work_mode'] == "production":
            api = Trading(config_file="credentials.yml", domain="api.ebay.com")
            pp_mail_address = cfg['pp_mail_address']['production']
        else:
            print("CANNOT DETERMINE WHICH WORK MODE TO USE. EXITTING")
            sys.exit()
        if cfg['debug']:
            log.info('Debug info: ')
            log.info('Title: ' + self.title)
            log.info('Manufacturer Part Number: ' + str(self.item.part_nr.rsplit(" ", 1)[0]))
            log.info('Year: ' + str(self.item.min_model_year) + " - " + str(self.item.max_model_year))
            log.info('Brand: ' + self.item.manufacturer)
            log.info('Reference OE/OEM Number: ' + str(self.item.oe_part_nr if not self.item.oe_part_nr_shortened else self.item.oe_part_nr_shortened))
            log.info('PayPalEmailAddress: ' + pp_mail_address)
            log.info('PrimaryCategory: ' + self.suggested_cat)
            log.info('StartPrice: ' + str(round(self.selling_price, 2)))
            log.info('PictureURL: ' + str(self.uploaded_img_urls))

        # api = Connection(config_file="config.yml", domain="api.ebay.com")
        # api = Connection(config_file="config.yml", domain="api.sandbox.ebay.com")
        # mini_app_list = str(generate_mini_app_list(applications)).replace("['", "").replace("']", "")
        # item_title = "12NEW " + title + " FOR " + mini_app_list + " " + oe_numbers1
        request = {
            "Item": {
                # "Title": "9NEW " + title + " FOR AUDI A6 100 " + " " + oe_numbers1,
                "Title": self.title,
                "Country": "LT",
                "Location": "Kaunas",
                "Site": "UK",
                "ConditionID": "1000",
                "ListingType": "FixedPriceItem",
                "Quantity": "2",
                "ProductListingDetails": {
                    # "EAN": "DoesNotApply"
                },
                "ItemSpecifics": {
                    "NameValueList": [
                        {"Name": "Manufacturer Part Number", "Value": str(self.item.part_nr.rsplit(" ", 1)[0])},
                        {"Name": "Year", "Value": str(self.item.min_model_year) + " - " + str(self.item.max_model_year)},
                        {"Name": "Brand", "Value": self.item.manufacturer},  # + " GERMANY"},
                        {"Name": "Reference OE/OEM Number", "Value": self.item.oe_part_nr if not self.item.oe_part_nr_shortened else self.item.oe_part_nr_shortened},
                        # {"Name": "Reference OE/OEM Number", "Value": self.item.oe_part_nr},
                    ]
                },
                # "PaymentMethods": [
                #     {"PaymentMethodType": "PayPal"},
                #     {"PaymentMethodType": "CreditCard"},
                # ],
                "PaymentMethods": [
                    "PayPal",
                    "CreditCard",
                ],
                # "PaymentMethods": ["CreditCard"],
                "PayPalEmailAddress": pp_mail_address,
                # "PayPalEmailAddress": "nobody@gmail.com",
                # "PrimaryCategory": {"CategoryID": "174030"},
                "PrimaryCategory": {"CategoryID": self.suggested_cat},
                # "Description": "<![CDATA[ " + description + "<br>" + "OE Part Numbers: "
                #               + oe_numbers1 + "<br><br>" + applications + " ]]>",
                "Description": self.description_html,
                "ListingDuration": "GTC",
                "StartPrice": round(self.selling_price, 2),
                "Currency": "GBP",
                "AutoPay": "False",
                # "AutoPaySpecified": "True",
                "PictureDetails": {
                    "GalleryType": "Gallery",
                    "PhotoDisplay": "SuperSize",
                    "PictureURL": self.uploaded_img_urls,
                },
                "ReturnPolicy": {
                    "ReturnsAcceptedOption": "ReturnsAccepted",
                    # "RefundOption": "MoneyBack",
                    "ReturnsWithinOption": "Days_30",
                    "ShippingCostPaidByOption": "Buyer"
                },
                "ShippingDetails": {
                    "ShippingServiceOptions": {
                        "FreeShipping": "True",

                        "ShippingService": "UK_EconomyShippingFromOutside"
                        # "ShippingService": "UK_SellersStandardInternationalRate"
                        # "ShippingService": "UK_IntlTrackedPostage"
                        # "ShippingService": "UK_StandardShippingFromOutside"
                        # "ShippingService": "UK_StandardInternationalFlatRatePostage"
                        # "ShippingService": "UK_TrackedDeliveryFromAbroad"
                        # "ShippingService": "UK_EconomyShippingFromOutside"
                    },
                    "InternationalShippingServiceOption": {
                        "ShipToLocation": "Worldwide",
                        "ShippingService": "UK_OtherCourierOrDeliveryInternational",
                        # "ShippingService": "UK_IntlTrackedPostage",
                        "ShippingServiceCost": "0"
                    }
                },
                # "ShipToLocations": "Worldwide",
                "DispatchTimeMax": "3"
            }
        }
        # request1 = {"Query": "9NEW " + title.replace(",", "") + " FOR AUDI A6 100 " + " " + oe_numbers1}
        # api.execute("GetSuggestedCategories", request1)
        try:
            res = api.execute("AddFixedPriceItem", request)
        except:
            log.error("[ITEM: " + self.item.part_nr + "]: Something wrong, cannot list item.")
        return res

    def fill_description_html(self):
        self.description_html = """
        <![CDATA[ 
            <title>eBay</title>
            <body marginwidth="0" marginheight="0">
                <table align="center" style="border-spacing: 0px; width: 100%;">
                    <tbody>
                    <tr>
                        <td>
                            <div id="ds_div">
                                <style type="text/css">
                                    body {
                                        font: 16px/1.5em "Overpass", "Open Sans", Helvetica, sans-serif;
                                        color: #333;
                                        font-weight: 300;
                                    }

                                    .table-sm th,
                                    .table-sm td {
                                        font-size: 13px;
                                        padding: 4px;
                                    }

                                    .description {
                                        margin-bottom: 3rem;
                                    }

                                    .description h2 {
                                        font-size: 1.2rem;
                                        font-weight: 600;
                                        padding: 0.5rem;
                                        color: #505050;
                                        padding-left: 1rem;
                                        border-bottom: 4px solid #ce212b;
                                    }

                                    .description .table td:first-child {
                                        padding-left: 1rem;
                                    }

                                    .tableFixHead          { overflow-y: auto!important; height: 550px; }
                                    .tableFixHead thead th { position: sticky; top: 0; }
                                </style>
                                <link rel="stylesheet"
                                      href="https://cdnjs.cloudflare.com/ajax/libs/materialize/0.98.0/css/materialize.min.css">
                                <link rel="stylesheet" href="https://use.fontawesome.com/releases/v5.2.0/css/all.css"
                                      integrity="sha384-hWVjflwFxL6sNzntih27bfxkr27PmbbK/iSvJ+a4+0owXq79v+lsFkW54bOGbiDQ"
                                      crossorigin="anonymous">
                                <div class="description">
                                    <center><img class="responsive-img"
                                         src="https://domain.lt/uploads1/logo.png"></center>
                                    <center><h2>""" + self.title + """</h2></center>
                                    <div class="row">
                                        <div class="col s12 m6">
                                            <div class="card">
                                                <div class="card-image">
                                                    <img class="responsive-img"
                                                         src='""" + self.hosted_img_url + """'>
                                                </div>
                                            </div>
                                        </div>
                                        <div class="col s12 m6">
                                            <div class="card-panel table-sm">
                                                <p class="header" style="color: #ce212b; font-size: 20px">Summary</p>
                                                <table class="striped bordered table-sm">
                                                    """ + self.summary_html + """
                                                </table>
                                            </div>
                                        </div>
                                        """ + self.details_html + """
                                    </div>
                                    <div class="row">
                                        <div class="col s24 m12">
                                            <div class="card-panel">
                                                <p class="header" style="color: #ce212b; font-size: 20px">Compatibility table</p>
                                                <div class="tableFixHead">
                                                     <table class="striped bordered table-sm">
                                                     """ + self.vehicles_html + """
                                                     </table>
                                                </div>
                                            </div>
                                         </div>
                                    </div>
                                    <div class="row">
                                        <div class="col s12 m6">
                                            <div class="card-panel">
                                                <p class="header" style="color: #ce212b; font-size: 20px">Will this item fit my vehicle?</p>
                                                If you have any questions about this or any other item, feel free to contact us on eBay, sending us information about your car (such as model, year, engine, VIN number) and we will be pleased to assist you choosing the right item for your car.
                                            </div>
                                         </div>
                                        <div class="col s12 m6">
                                            <div class="card-panel">
                                                <p class="header" style="color: #ce212b; font-size: 20px">Reference Numbers</p>
                                                    """ + str(self.item.analog_part_nr).replace("'", "").replace(",", "").replace("[", "").replace("]", "") + """
                                            </div>
                                         </div>
                                    </div>
                                    <div class="row">
                                        <div class="col s12 m6">
                                            <div class="card-panel">
                                                <p class="header" style="color: #ce212b; font-size: 20px">Shipping</p>
                                                We provide a Worldwide shipping. The dispatch takes maximum 3 business days. Usually, we dispatch the item the next business day.<br><br><br>
                                            </div>
                                         </div>
                                        <div class="col s12 m6">
                                            <div class="card-panel">
                                                <p class="header" style="color: #ce212b; font-size: 20px">Payments</p>
                                                We accept payment methods listed below:
                                                <br>1. PayPal
                                                <br>2. Credit cards<br><br>
                                            </div>
                                        </div>
                                    </div>
                                    <div class="row">
                                        <div class="col s12 m6">
                                            <div class="card-panel">
                                                <p class="header" style="color: #ce212b; font-size: 20px">Returns</p>
                                                We provide a simple return policy:
                                                <br>1. We cannot process a return as long as you have not contacted us on ebay first.
                                                <br>2. We accept a return only in cases when the item is genuinely faulty or in pristine condition (i.e., have not been fitted and in original unmarked packaging).
                                                <br>3. A return will not be processed if the item has been dispatched 30 days ago, unless specifically agreed beforehand.
                                                <br>4. We will process your return within 2 business days and will act quickly on agreed conditions over messages (e.g., refund, replacement or exchange).
                                            </div>
                                         </div>
                                        <div class="col s12 m6">
                                            <div class="card-panel">
                                                <p class="header" style="color: #ce212b; font-size: 20px">Feedback</p>
                                                Once we receive an order, the feedback is automatically sent to you. We appreciate a positive feedback so let the people know about your pleasant experience while buying from us. <br>
                                                If we do not deserve a positive feedback, please let us know first before before leaving the negative one. We will solve the issues and make your buying experience better.<br><br><br><br>
                                            </div>
                                         </div>
                                    </div>
                                </div>
                            </div>
                    </tbody>
                </table>
            </body>
        ]]>"""
