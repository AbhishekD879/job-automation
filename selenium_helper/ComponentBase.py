import logging
from collections import OrderedDict

from selenium.common import NoSuchElementException, StaleElementReferenceException, WebDriverException

from selenium_helper.globals import get_driver, parse_pattern, find_element, VoltronException, find_elements, wait_for_result


def scroll_to_center_of_element(web_element):
    get_driver().execute_script("return arguments[0].scrollIntoView({ behavior: 'instant', block: 'center' });",
                                web_element)


class ComponentBase(object):
    _context_timeout = 15
    _pattern_values = {}
    _list_item_type = None

    def __init__(self, selector='', context=None, web_element=None, timeout=_context_timeout, pattern_values=None,
                 *args,
                 **kwargs):
        self._item = None
        self._logger = logging.getLogger('voltron_logger')
        self._args, self._kwargs = args, kwargs
        self._context = context if context is not None else get_driver()
        self._selector = selector
        self._timeout = timeout
        if isinstance(pattern_values, dict):
            self._pattern_values.update(pattern_values)
        if web_element is not None:
            self._we = web_element
        else:
            if self._pattern_values:
                selector = parse_pattern(selector, pattern_values=self._pattern_values)
            self._selector = selector
            self._we = self._find_myself(timeout=self._timeout)

    def _find_element_by_selector(self, selector='', context=None, pattern_values=None,
                                  bypass_exceptions=(
                                          NoSuchElementException, StaleElementReferenceException, WebDriverException),
                                  timeout=10):
        context = self._we if context is None else context

        selector = parse_pattern(selector, pattern_values=pattern_values) if pattern_values else selector
        element = find_element(selector=selector, context=context, bypass_exceptions=bypass_exceptions, timeout=timeout)
        return element

    def _find_myself(self, timeout=_context_timeout):
        element = self._find_element_by_selector(selector=self._selector, context=self._context, timeout=timeout)
        if not element:
            raise VoltronException(f'"{self.__class__.__name__}" component not found')
        return element

    def _find_elements_by_selector(self, selector='', context=None, pattern_values=None,
                                   bypass_exceptions=(
                                           NoSuchElementException, StaleElementReferenceException, WebDriverException),
                                   timeout=25):
        context = self._we if context is None else context
        selector = parse_pattern(selector, pattern_values=pattern_values) if pattern_values else selector
        elements = find_elements(selector=selector, context=context, bypass_exceptions=bypass_exceptions,
                                 timeout=timeout)
        if elements is None:
            return []
        return elements

    def wait_for_element_disappear(self, we=None, timeout=10):
        if we is None:
            self._logger.warning(
                f'*** Nothing passed to wait for element disappear function "{self.__class__.__name__}"')
            we = self._we

        def check_disappear(webelement):
            try:
                return not webelement.is_displayed()
            except StaleElementReferenceException:
                return True
            except NoSuchElementException:
                return True

        return wait_for_result(lambda: check_disappear(webelement=we), timeout=timeout,
                               name=f'WebElement "{self.__class__.__name__}" to disappear')

    def scroll_to_bottom(self):
        drv = get_driver()
        drv.execute_script("window.scrollTo(0,document.body.scrollHeight);")

    def scroll_to_top(self):
        drv = get_driver()
        drv.execute_script("window.scrollTo(0,0);")

    def _get_webelement_text(self, selector='', we=None, context=None, pattern_values=None, timeout=0) -> str:
        try:
            if we:
                return self._we_text(we)
            elif selector is not None and selector != '':
                selector = parse_pattern(selector, pattern_values=pattern_values) if pattern_values else selector
                we = self._find_element_by_selector(selector=selector, context=context, timeout=timeout)
                return self._we_text(we) if we else ''
            else:
                raise VoltronException(
                    'Internal error: No selector or webelement passed to get_webelement_text function')
        except StaleElementReferenceException:
            we = self._find_element_by_selector(selector=selector, context=context, timeout=timeout)
            self._we = we
            return self._we_text(we) if we else ''
        except Exception as err:
            raise VoltronException(f'Error getting WebElement text. Exception string: "{err}"')

    def _we_text(self, we):
        try:
            if self.is_safari:
                return we.get_attribute('innerText').strip('\n').strip()
            else:
                return we.text
        except Exception as err:
            return we.get_attribute('innerText').strip('\n').strip()

    def _wait_for_not_empty_web_element_text(self, selector='', we=None, context=None, pattern_values=None, name=None,
                                             timeout=0):
        return wait_for_result(lambda: self._get_webelement_text(selector, we, context, pattern_values, timeout=0),
                               name=name if name else f'Waiting while text of {selector} is not empty',
                               timeout=timeout)

    @property
    def items(self):
        items_we = self._find_elements_by_selector(selector=self._item, context=self._we, timeout=self._timeout)
        self._logger.debug(
            f'*** Found {len(items_we)} {self.__class__.__name__} - {self._list_item_type.__name__} items')
        items_array = []
        for item_we in items_we:
            if item_we.is_displayed():
                item_component = self._list_item_type(web_element=item_we)
                items_array.append(item_component)
        return items_array

    @property
    def items_names(self):
        return list(self.items_as_ordered_dict.keys())

    def click_item(self, item_name: str, timeout: int = 5):
        if not item_name:
            raise VoltronException('Item name was not specified')

        item_found = wait_for_result(lambda: next((item for item_name_, item in self.items_as_ordered_dict.items()
                                                   if item_name_.upper().strip() == item_name.upper()), None),
                                     timeout=timeout,
                                     name=f'Specified "{item_name}" to appear between items')
        if not item_found:
            raise VoltronException(
                f'"{self.__class__.__name__}" item: "{item_name}" not found in items list: {self.items_names}')
        item_found.click()

    @property
    def has_items(self):
        items_we = self._find_elements_by_selector(selector=self._item, context=self._we, timeout=self._timeout)
        return bool(items_we)

    @property
    def first_item(self):
        item_we = self._find_element_by_selector(selector=self._item, context=self._we, timeout=self._timeout)
        if not item_we:
            return (None, None)
        list_item = self._list_item_type(web_element=item_we)
        return (list_item.name, list_item)

    def n_items_as_ordered_dict(self, no_of_items=5) -> OrderedDict:
        items_we = self._find_elements_by_selector(selector=self._item, context=self._we, timeout=self._timeout)
        self._logger.debug(
            f'*** Found {len(items_we)} {self.__class__.__name__} - {self._list_item_type.__name__} items')
        n_items_ordered_dict = OrderedDict()
        for item_we in items_we[:no_of_items]:
            list_item = self._list_item_type(web_element=item_we)
            list_item.scroll_to()
            n_items_ordered_dict.update({list_item.name: list_item})
        return n_items_ordered_dict

    @property
    def count_of_items(self):
        return len(self._find_elements_by_selector(selector=self._item, context=self._we, timeout=self._timeout))

    @property
    def items_as_ordered_dict(self) -> OrderedDict:
        items_we = self._find_elements_by_selector(selector=self._item, context=self._we, timeout=self._timeout)
        self._logger.debug(
            f'*** Found {len(items_we)} {self.__class__.__name__} - {self._list_item_type.__name__} items')
        items_ordered_dict = OrderedDict()
        for item_we in items_we:
            list_item = self._list_item_type(web_element=item_we)
            list_item.scroll_to()
            items_ordered_dict.update({list_item.name: list_item})
        return items_ordered_dict

    def scroll_to(self):
        self.scroll_to_we()

    def click(self):
        self.scroll_to_we()
        try:
            self.perform_click()
        except WebDriverException as e:
            raise VoltronException(f'Can not click on {self.__class__.__name__}. {e}')

    def perform_click(self, we=None):
        self._logger.debug(
            f'*** User has clicked "{self._we.text}" button. Call "{self.__class__.__name__}.click" method'
        )
        we = we if we else self._we
        try:
            we.click()
        except:
            # This is JS Click
            # Please Implement Javascript Click if Not Implemented
            get_driver().execute_script("arguments[0].click()", self._we)

    def is_displayed(self, expected_result=True, timeout=1, poll_interval=0.5, name=None, scroll_to=True,
                     bypass_exceptions=(NoSuchElementException, StaleElementReferenceException)) -> bool:
        if not name:
            name = f'"{self.__class__.__name__}" displayed status is: {expected_result}'
        self.scroll_to_we() if scroll_to else None

        result = wait_for_result(lambda: self._we.is_displayed(),
                                 expected_result=expected_result,
                                 timeout=timeout,
                                 poll_interval=poll_interval,
                                 bypass_exceptions=bypass_exceptions,
                                 name=name)
        return result

    def is_selected(self, expected_result=True, timeout=2, poll_interval=0.5, name=None) -> bool:
        if not name:
            name = f'"{self.__class__.__name__}" selected status is: {expected_result}'
        result = wait_for_result(lambda: 'active' in self.get_attribute('class').strip(' ').split(' '),
                                 expected_result=expected_result,
                                 timeout=timeout,
                                 poll_interval=poll_interval,
                                 name=name)
        return result

    def is_disabled(self, *args, **kwargs):
        raise VoltronException('Deprecated method "is_disabled", use "is_enabled" instead')

    def is_active(self, *args, **kwargs):
        raise VoltronException('Deprecated method "is_active", use "is_selected" instead')

    def is_enabled(self, expected_result=True, timeout=1, poll_interval=0.5, name=None,
                   bypass_exceptions=(NoSuchElementException, StaleElementReferenceException, TypeError)) -> bool:
        if not name:
            name = f'"{self.__class__.__name__}" enabled status is: {expected_result}'

        def _is_enabled(we):
            if we.get_attribute('disabled') is not None:
                return any([False for status in ('true', 'disabled') if status in we.get_attribute('disabled')])
            elif 'disabled' in we.get_attribute('class').strip(' ').split(' '):
                return False
            else:
                return True

        result = wait_for_result(lambda: _is_enabled(we=self._we),
                                 expected_result=expected_result,
                                 timeout=timeout,
                                 poll_interval=poll_interval,
                                 name=name,
                                 bypass_exceptions=bypass_exceptions)
        return result

    def scroll_to_we(self, web_element=None):
        if web_element is None:
            self._logger.debug(
                f'*** Nothing passed to scroll function, scrolling to current web element "{self.__class__.__name__}"')
            web_element = self._we
        # Use js to scroll to current web element
        scroll_to_center_of_element(web_element)

    def get_attribute(self, attribute):
        result = self._we.get_attribute(attribute)
        self._logger.debug(f'*** Found attribute "{result}" for {self.__class__.__name__}')
        return result
