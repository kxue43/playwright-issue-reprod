"""
Script Name: helper.py

Description: Provide helper functions to the other modules

Interpreter Version: Python 3.9.7 Windows 64-bit

External Dependencies: Playwright
"""
# Built-in
from pathlib import Path
import re
import sqlite3

# External
from playwright.sync_api import Browser, Page


class PageManager:
    """"
    Context manager class for the Playwright Page object.
    """
    def __init__(
        self,
        browser: Browser,
        auto_dialogue: bool = False,
        accept_downloads: bool = True
    ) -> None:
        self.browser = browser
        self.auto_diaglogue = auto_dialogue
        self.accept_downloads = accept_downloads

    def __enter__(self) -> Page:
        self.context = self.browser.new_context(
            accept_downloads=self.accept_downloads
        )
        self.page = self.context.new_page()
        if self.auto_diaglogue:
            self.page.on("dialog", lambda dialog: dialog.accept())
        return self.page

    def __exit__(self, *args, **kwargs) -> None:
        self.context.close()


class ConnectionManager:
    """
    Context manager class for the SQLite3 database connection.
    """
    def __init__(self, db_path: Path) -> None:
        self.db_path = db_path
        if db_path.exists():
            db_path.unlink()

    def __enter__(self) -> sqlite3.Connection:
        self.con = sqlite3.connect(self.db_path)
        self.con.row_factory = sqlite3.Row
        cur = self.con.cursor()
        file_dir = Path(__file__).parent
        sql_path = file_dir.joinpath('qcor_mh.sql')
        execute_ddl_script(sql_path, self.con, cur)
        cur.close()
        return self.con

    def __exit__(self, *args, **kwargs) -> None:
        self.con.close()


table = re.compile(r'\s*create table +(\w+) *\(', flags=re.I | re.A)


def execute_ddl_script(
    inpath: Path, con: sqlite3.Connection, cur: sqlite3.Cursor
) -> str:
    """
    Execute a DDL script and return the name of the table thus created.

    Parameters:
        inpath (Path): path to the SQL script
        con (Connection): the Connection object in PEP 249
        cur (Cursor): the Cursor object in PEP 249

    Returns:
        table_name (str): the name of the table created by the DDL script
    """
    with open(inpath, 'r') as fr:
        script = fr.read()
    cur.execute(script)
    con.commit()
    table_name = ''
    with open(inpath, 'r') as fr:
        line = fr.readline()
        while line != '' and not isinstance(table.match(line), re.Match):
            line = fr.readline()
    result = table.match(line)
    if isinstance(result, re.Match):
        table_name = result.group(1).strip()
    if table_name != '':
        return table_name
    else:
        raise Exception("Cannot identify table name from DDL script.")
