import logging
import pathlib
from contextlib import contextmanager
from decimal import Decimal
from typing import List

from selenium import webdriver
from src.gamedeals import Utility, ini_parser
from src.gamedeals.BundleHandlers import HumbleBundleHandler
from src.gamedeals.Product import Game
from src.gamedeals.StoreHandlers import FanaticalHandler, HumbleStoreHandler
from src.gamedeals.TelegramSender import TelegramSender


@contextmanager
def managed_chromedriver(options):
    try:
        chrome_driver = webdriver.Chrome(options=options)
        yield chrome_driver
    finally:
        chrome_driver.quit()


if __name__ == "__main__":
    pathlib.Path('./logs').mkdir(parents=True, exist_ok=True)
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s  %(message)s",
        handlers=[
            logging.FileHandler("./logs/GameDeals.log"),
            logging.StreamHandler()
        ])
    logger = logging.getLogger()

    telegram = TelegramSender()
    opts = webdriver.ChromeOptions()
    opts.add_argument('--disable-notifications')
    opts.add_argument('headless')
    with managed_chromedriver(opts) as driver:
        driver.set_window_size(1800, 1070)
        driver.implicitly_wait(2)
        fanatical_games: List[Game] = FanaticalHandler.crawl(driver)
        for game in fanatical_games:
            FanaticalHandler.set_game_data(driver, game)
        humble_games: List[Game] = HumbleStoreHandler.crawl(driver)
        for game in humble_games:
            HumbleStoreHandler.set_game_data(game, driver)
        game_list = fanatical_games + humble_games
        for game in game_list:
            if game.profit_margin > ini_parser.get_net_profit_percentage():
                telegram.send_message(
                    f"Game deal found:\n name: {game.name}\n price: {game.sale_price}\n prifit margin: {game.profit_margin * 100}%\n url: {game.url}")

        humble_bundles = HumbleBundleHandler.crawl(driver)
        for bundle in humble_bundles:
            HumbleBundleHandler.set_bundle_data(driver, bundle)
        bundle_list = humble_bundles
        for bundle in bundle_list:
            if bundle.profit_margin > ini_parser.get_net_profit_percentage():
                telegram.send_message(
                    f"Bundle deal found:\n name: {bundle.name}\n price: {bundle.sale_price}\n prifit margin: {bundle.profit_margin * 100}%\n url: {bundle.url}")
