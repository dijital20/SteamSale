from urllib import request
from sys import argv, stdout
from re import sub
from operator import itemgetter
from datetime import datetime
from time import sleep

from bs4 import BeautifulSoup

# Initialize logging ----------------------------------------------------------
import logging

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
log_formatter = logging.Formatter('%(asctime)s <%(levelname)s> <%(module)s.%(funcName)s> %(message)s')
log_handler = logging.StreamHandler(stdout)
log_handler.setLevel(logging.DEBUG)
log_handler.setFormatter(log_formatter)
logger.addHandler(log_handler)


class SteamSale:
    store_url = 'http://store.steampowered.com'

    def __init__(self):
        logger.debug('Getting initial list of sale items...')
        self.sale_items = self.parse_store()
        logger.debug('Done getting initial list of sale items.\n')

    def loop(self):
        logger.debug('Starting loop.')
        print(self.sale_items_string)
        while 1:
            curr_sale_items = self.parse_store(text=False)
            if curr_sale_items != self.sale_items:
                print('Sale items have changed!!')
                self.sale_items = curr_sale_items
                print(self.sale_items_string)
            # Wait 5 mins before refreshing the list.
            sleep(300)
        logger.debug('Stopping loop.')

    def parse_store(self, text=True):
        if text:
            print('Getting items', end='', flush=True)
        sale_items = list()
        store_content = request.urlopen(self.store_url).read()
        soup = BeautifulSoup(store_content)
        for idx, div_item in enumerate(soup.find_all('div', 'summersale_dailydeal_ctn')):
            logger.debug('Parsing item {}'.format(idx))
            parent = div_item.parent['class'][0]
            if text:
                print('.', end='', flush=True)
            sale_item = dict()
            try:
                sale_item['game_name'] = self.get_game_name(div_item)
                sale_item['game_price'] = div_item.find('div', 'discount_final_price').string
                sale_item['game_orig_price'] = div_item.find('div', 'discount_original_price').string
                sale_item['game_discount'] = div_item.find('div', 'discount_pct').string
            except AttributeError:
                pass
            if sale_item not in sale_items:
                logger.debug('Adding item {} ({}) to sale_items'.format(sale_item['game_name'], idx))
                sale_items.append(sale_item)
            else:
                logger.debug('Item {} already exists. Skipping.'.format(sale_item['game_name']))
        if text:
            print('\n')
        sale_items.sort(key=itemgetter('game_name'))
        return sale_items

    @staticmethod
    def get_game_name(item_soup):
        """
        Get the name of a game based on its HTML fragment from Beautiful Soup.

        :param item_soup: BeautifulSoup
        :return: string
        """
        logger.debug('Getting name')
        game_name = None
        strip_pattern = '^(Save) [0-9]*\%* (on)+ '
        try:
            # Get the URL
            game_url = item_soup.find('a', 'summersale_dailydeal')['href']
            # Get the page content and parse it.
            game_soup = BeautifulSoup(request.urlopen(game_url))
            # Set the name
            game_name = game_soup.find('title').string
            game_name = sub(strip_pattern, '', game_name).replace('on Steam', '')
        except (TypeError, AttributeError):
            logger.debug('item_soup must not have been a BeautifulSoup item, or game_soup could not find a div with '
                  'apphub_AppName.')
        logger.debug('Returning {}'.format(game_name))
        return game_name

    @property
    def sale_items_string(self):
        """
        Compile the list of dictionaries self.sale_items to a pretty string for displaying.
        :return: string
        """
        out_string = 'Games on Sale ({})\n{:=^80}\n'.format(datetime.now(), '')
        for i in self.sale_items:
            if len(i) == 4:
                out_string += '{game_name:.<58}{game_price:.>7} ({game_orig_price:>7}){game_discount:>5}\n'.format(**i)
        return out_string

    def dump_store_html(self):
        store_content = request.urlopen(self.store_url).read()
        soup = BeautifulSoup(store_content)
        with open('store_content.html', mode='w') as f:
            f.write(soup.prettify())
        print('Wrote store_content.html')


if __name__ == '__main__':
    if '--debug' in argv:
        print('Setting log level to DEBUG.')
        logger.setLevel(logging.DEBUG)
    
    app = SteamSale()
    if '--dump' in argv:
        app.dump_store_html()
    
    if '--loop' in argv:
        print('Looping. Press Ctrl + C to quit.')
        try:
            app.loop()
        except KeyboardInterrupt:
            print('\nExiting.')
    else:
        print(app.sale_items_string)