from time import sleep

from selenium.common import InvalidElementStateException, ElementNotInteractableException
from selenium.webdriver import Keys

from selenium_helper.ComponentBase import ComponentBase
from selenium_helper.globals import wait_for_result, get_driver


def get_value(web_element):
    return get_driver().execute_script("return arguments[0].value;", web_element)


def set_value(_we, param):
    script = """
    arguments[0].setAttribute('value', arguments[1]);
    arguments[0].value = arguments[1];
    arguments[0].dispatchEvent(new Event('change'));
    """
    driver = get_driver()
    driver.execute_script(script, _we, param)


class InputBase(ComponentBase):
    _send_keys_delay = 0.1

    @property
    def value(self):
        self.scroll_to_we()
        value = wait_for_result(lambda: get_value(self._we),
                                timeout=0.6,
                                name='Value to appear')
        return value

    @value.setter
    def value(self, value):
        self.scroll_to_we()
        driver = get_driver()
        try:
            self._we.clear()
            self.send_keys(str(value))
        except (InvalidElementStateException, ElementNotInteractableException):
            driver.execute_script("arguments[0].value='';arguments[0]", self._we)
            driver.execute_script(f"arguments[0].value={value};arguments[0].dispatchEvent(new Event('change'));",
                                  self._we)
        self._logger.debug(
            f'*** User has set "{value}" on Input. Call of "{self.__class__.__name__}"'
        )
        try:
            self._we.send_keys(Keys.SHIFT + Keys.TAB)
        except (InvalidElementStateException, ElementNotInteractableException):
            pass
        wait_for_result(lambda: str(self.value) == str(value),
                        timeout=1,
                        name=f'{self.__class__.__name__} value to appear')
        # try:
        #     if tests.settings.device_type == 'mobile' and tests.use_browser_stack:
        #         get_driver().hide_keyboard()
        # except Exception as e:
        #     self._logger.warning(f'*** Unable to hide keyboard: {e}')

    @property
    def placeholder(self):
        return self.get_attribute('placeholder')

    def clear(self):
        set_value(self._we, '')
        value = get_value(self._we)
        if value:
            self._we.clear()

    def send_keys(self, keys, delay=_send_keys_delay):
        for symbol in str(keys):
            self._we.send_keys(symbol)
            sleep(delay)

    def is_active(self, expected_result=True, timeout=1):
        return wait_for_result(lambda: self._we.is_displayed() and self._we.is_enabled(),
                               expected_result=expected_result,
                               timeout=timeout,
                               name=f'Amount input active status to be "{expected_result}"')
