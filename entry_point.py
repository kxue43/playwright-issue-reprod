# Built-in
from pathlib import Path

# External
from playwright.sync_api import sync_playwright

# Own
from helper import PageManager, ConnectionManager
from scraper import QcorTableScraper


if __name__ == '__main__':
    file_dir = Path(__file__).parent
    with ConnectionManager(file_dir.joinpath('qcor.db')) as con:
        cur = con.cursor()
        with sync_playwright() as plwrt:
            browser = plwrt.chromium.launch(headless=True)
            with PageManager(browser, auto_dialogue=True) as page:
                QcorTableScraper.initialize(
                    file_dir,
                    '2021',
                    page,
                    con,
                    cur
                )
                agent = QcorTableScraper()
                agent.scrape_table()
