# Potential Issue with Playwright v1.21.0 on handling popups in headless mode

This is the reproduction repo to report a potential issue about handling popups in headless mode with
Playwright v1.21.0. The program automates the collection of public data from a government website. It is
part of a larger project that I'm working on for my employer. I've obtained permission to publish this repo.

## Update

**It has been verified that it is not a bug of Playwright, but due to the bot protection mechanism of the target website.**

## Environments

- OS: Windows 10 64-bit

- Python version: 3.9.7

- Playwright version: 1.21.0

## Running the program

- Playwright v1.21.0 is the only dependency

- Chromium is the browser used.

- `python entry_point.py`

## The issue spotted

`scraper.QcorTableScraper.handle_one_popup()` contains the code for triggering and handling popup pages. I used the
code snippet found on [Playwright Docs on popups](https://playwright.dev/python/docs/pages#handling-popups). The
while loop is for automatic retry when a `TimeoutError` is raised during the triggering of a popup page.

When running the program in headless mode, every such triggering of popup raises a `TimeoutError`. However,
when running in headed mode (`entry_point.py` line 17, changing `True` to `False`), everything works perfectly.

The `no-no-popup-exception-handling` branch contains pretty much the same code, except that automatic retry 
is removed from `scraper.QcorTableScraper.handle_one_popup()`. The result is similar. Headless mode raises a
`TimeoutError`; headed mode works well.

The target website is [QCOR](https://qcor.cms.gov/main.jsp).

I've looked at the official docs on `browser_type.launch()` and `browser.new_context()` and did not find anything
related to configurations of popup-handling.
