"""
Script Name: scraper.py

Description: Scrape Community Mental Health Centers (CMHCs) information
from https://qcor.cms.gov/main.jsp and save the result in a SQLite table.

Interpreter Version: Python 3.9.7 Windows 64-bit

External Dependencies: playwright
"""
# Built-in
from pathlib import Path
import re
from sqlite3 import Connection, Cursor
from typing import cast, ClassVar

# External
from playwright.sync_api import Locator, Page, TimeoutError


QCOR_URL = 'https://qcor.cms.gov/main.jsp'
ADDR_LINE2_TD_TMPLT = 'xpath=//html/body/div[3]/table/tbody/tr[{}]/td[2]'
OTHER_TD_TMPLT = 'xpath=//html/body/div[3]/table/tbody/tr[{}]/td'
CITY_STATE_ZIP = re.compile(r'(.+), *([A-Z]{2}) +([0-9]{5})')


def handle_one_mh_popup(popup: Page, cur: Cursor) -> None:
    ccn = popup.locator(OTHER_TD_TMPLT.format(2)).inner_text().strip()
    provider_name = popup.locator(OTHER_TD_TMPLT.format(1)).inner_text().strip()
    address = popup.locator(OTHER_TD_TMPLT.format(4)).inner_text().strip()
    address_line2 = popup.locator(ADDR_LINE2_TD_TMPLT.format(5)).inner_text().strip()
    match = CITY_STATE_ZIP.search(address_line2)
    city = None
    state = None
    zip_code = None
    if isinstance(match, re.Match):
        city = match.group(1)
        state = match.group(2)
        zip_code = match.group(3)
    participation_date = popup.locator(OTHER_TD_TMPLT.format(7)).inner_text().strip()
    cur.execute(
        """
        INSERT INTO qcor_mh
        (
            "CCN",
            "Provider Name",
            "Address",
            "City",
            "State",
            "Zip Code",
            "Provider Type",
            "Original Participation Date"
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?);
        """,
        (
            ccn,
            provider_name,
            address,
            city,
            state,
            zip_code,
            'Home Health Agency',
            participation_date
        )
    )


def go_to_mental_health_table_view(page: Page, calendar_year: str) -> None:
    print('before navigating to target view of website')
    print('userAgent:', page.evaluate('() => window.navigator.userAgent'))
    print('window.is_nav:', page.evaluate('() => window.is_nav'))
    print('window.is_nav5up:', page.evaluate('() => window.is_nav5up'))
    print('window.is_ie:', page.evaluate('() => window.is_ie'))
    active_count_xpath = 'xpath=//html/body/table/tbody/tr[4]/td[1]/table/tbody/tr[1]/td/table/tbody/tr[4]/td/a'
    section_xpath = 'xpath=//html/body/table/tbody/tr[4]/td[1]/table/tbody/tr[1]/td/table[3]/tbody/tr[6]/td/a'
    try:
        page.goto(QCOR_URL)
        page.wait_for_load_state('networkidle')
        page.click(section_xpath)
    except TimeoutError:
        page.goto(QCOR_URL)
        page.wait_for_load_state('networkidle')
        page.click(section_xpath)
    page.click(active_count_xpath)
    page.select_option('xpath=//select[@id="year_type"]', value='CY')
    page.select_option('xpath=//select[@id="begin_year"]', value=calendar_year)
    page.select_option('xpath=//select[@id="end_year"]', value=calendar_year)
    page.click('xpath=//html/body/div[2]/form[1]/table[2]/tbody/tr[2]/td/input')
    page.wait_for_load_state('networkidle')


class QcorTableScraper:
    scraped_qcor_dir: ClassVar[Path]
    calendar_year: ClassVar[str]
    page: ClassVar[Page]
    con: ClassVar[Connection]
    cur: ClassVar[Cursor]
    tr_loc: ClassVar[Locator]
    tr_a_tmplt: ClassVar[str]
    l1_tr_count: int
    current_l2_tr_count: int
    current_l3_tr_count: int
    current_l1_order: int
    current_l2_order: int
    current_l3_order: int

    def __init__(self) -> None:
        self.current_l2_tr_count = 0
        self.current_l3_tr_count = 0
        self.current_l1_order = 0
        self.current_l2_order = 0
        self.current_l3_order = 0

    @classmethod
    def initialize(
        cls,
        scraped_qcor_dir: Path,
        calendar_year: str,
        page: Page,
        con: Connection,
        cur: Cursor
    ) -> None:
        cls.scraped_qcor_dir = scraped_qcor_dir
        cls.calendar_year = calendar_year
        cls.page = page
        cls.con = con
        cls.cur = cur
        cls.tr_loc = cls.page.locator('xpath=//html/body/div[2]/table[2]/tbody/tr')
        cls.tr_a_tmplt = 'xpath=//html/body/div[2]/table[2]/tbody/tr[{}]//a'

    def get_tr_count(self) -> int:
        return self.tr_loc.count()

    def get_target_l2_tr_index(self) -> int:
        return self.current_l1_order + self.current_l2_order + self.current_l3_tr_count

    def get_target_l3_tr_index(self) -> int:
        return self.current_l1_order + self.current_l2_order + self.current_l3_order

    def handle_one_popup(self, l3_tr_a_selector: str) -> None:
        count = 1
        while count <= 5:
            try:
                with self.page.expect_popup() as popup_info:
                    self.page.click(l3_tr_a_selector)
                popup = popup_info.value
                popup.wait_for_load_state()
            except TimeoutError:
                print('stuck!')
                print(l3_tr_a_selector)
                try:
                    self.page.reload(wait_until='networkidle')
                except TimeoutError:
                    self.page.wait_for_load_state('networkidle')
                count += 1
            else:
                handle_one_mh_popup(popup, self.cur)
                popup.close()
                return

    def scrape_table(self) -> None:
        go_to_mental_health_table_view(self.page, self.calendar_year)
        print('after navigating to target view of website')
        print('userAgent:', self.page.evaluate('() => window.navigator.userAgent'))
        print('window.is_nav:', self.page.evaluate('() => window.is_nav'))
        print('window.is_nav5up:', self.page.evaluate('() => window.is_nav5up'))
        print('window.is_ie:', self.page.evaluate('() => window.is_ie'))
        l1_loc = self.page.locator('xpath=//html/body/div[2]/table[2]/tbody/tr[@class="tblAlt"]')
        self.l1_tr_count = cast(int, l1_loc.count())
        for i in range(self.l1_tr_count):
            self.current_l1_order = i + 1
            l1_loc.nth(i).locator('xpath=/th/a').click()
            self.page.wait_for_load_state('networkidle')
            self.current_l2_tr_count = self.get_tr_count() - self.l1_tr_count - 1
            self.current_l2_order = 1
            self.current_l3_tr_count = 0
            for _ in range(self.current_l2_tr_count):
                self.page.click(self.tr_a_tmplt.format(self.get_target_l2_tr_index()))
                self.page.wait_for_load_state('networkidle')
                self.current_l3_tr_count = self.get_tr_count() - self.l1_tr_count - 1 - self.current_l2_tr_count
                self.current_l3_order = 1
                for _ in range(self.current_l3_tr_count):
                    self.handle_one_popup(self.tr_a_tmplt.format(self.get_target_l3_tr_index()))
                    self.current_l3_order += 1
                self.current_l2_order += 1
        self.con.commit()
