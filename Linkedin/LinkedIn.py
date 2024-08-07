from selenium.webdriver.common.by import By

from selenium_helper.ComponentBase import ComponentBase
from selenium_helper.InputBase import InputBase
from selenium_helper.globals import find_element, get_driver


class LinkedIn:
    _url = "https://www.linkedin.com/feed/"
    _search_bar = 'xpath=//*[@id="global-nav-typeahead"]'

    def __init__(self, *args, **kwargs):
        self.driver = get_driver()
        self.driver.get(self._url)

    @property
    def search(self):
        return InputBase(selector=self._search_bar, context=self._we, timeout=5)
