import inspect
import logging
import re
from time import time, sleep


from selenium.common import NoSuchElementException, StaleElementReferenceException, WebDriverException, \
    InvalidSelectorException
from selenium.webdriver.chrome.webdriver import WebDriver
from selenium.webdriver.common.by import By

_logger = logging.getLogger(name='voltron_logger')
driver = None


def wait_for_result(
        func,
        fargs=(),
        fkwargs=None,
        name=None,
        poll_interval=0.5,
        expected_result=True,
        bypass_exceptions=(NoSuchElementException, StaleElementReferenceException),
        timeout=30
):
    if name is None:
        name = func.__name__
    logger = logging.getLogger('voltron_logger')
    if not fkwargs:
        fkwargs = {}
    sleeping_time = 0
    if not isinstance(expected_result, bool):
        raise VoltronException(f'Expected result should be True or False, instead it is {expected_result}')
    result = None
    waiting_time = time()
    period = poll_interval / 2
    time_to_stop = time() + (timeout if timeout > period else period)
    try:
        caller_name = inspect.stack()[1].function
    except RuntimeError:
        caller_name = inspect.stack()[1].function
    while waiting_time < time_to_stop:
        try:
            result = func(*fargs, **fkwargs)
            if bool(result) is expected_result:
                logger.info(
                    f'[{caller_name}] Condition "{name}" succeed with result "{bool(result)}" in {sleeping_time} sec')
                return result

        except bypass_exceptions as err:
            logger.debug(
                f'[{caller_name}] Overriding bypassed "{err.__class__.__name__}" exception in WAIT with message:\n"{err}"')
        logger.debug(f'Waiting {sleeping_time} sec for condition "{name}" to result "{expected_result}",'
                     f' current is "{bool(result)}"')

        sleeping_time += poll_interval
        waiting_time += poll_interval
        sleep(poll_interval)

    else:
        logger.debug(
            f'[{caller_name}] Failed waiting for condition "{name}" to result "{expected_result}" in {sleeping_time} sec')
    return result


def set_driver(value: WebDriver):
    global driver
    driver = value


def get_driver() -> WebDriver:
    return driver


class GeneralException(Exception):
    pass


def parse_selector(selector=''):
    by = {
        'css': By.CSS_SELECTOR,
        'xpath': By.XPATH,
        'id': By.ID,
        'name': By.NAME,
        'tag': By.TAG_NAME,
    }
    if not isinstance(selector, str):
        raise GeneralException(f'Selector should be a string value got "{selector}" with type "{type(selector)}"')
    matcher = re.match(r'^([a-z]+)=(.+)', selector)
    # TODO: allow whitespace characters in xpath, e.g.: xpath = .//*
    if matcher is not None and matcher.lastindex == 2:
        sector_type = matcher.group(1)
        selector_string = matcher.group(2)
        if sector_type in by.keys():
            return (by[sector_type], selector_string)
        else:
            raise GeneralException(f'Unknown selector type "{sector_type}"')
    else:
        raise GeneralException(f"Selector doesn't match pattern 'xpath=//*', given '{selector}'")


class VoltronException(Exception):
    pass


def parse_pattern(pattern_data='', pattern_values={}):
    names = re.findall(r'{([a-zA-Z0-9]+)}', pattern_data)
    for name in names:
        try:
            pattern_data = pattern_data.replace('{%s}' % name, pattern_values[name])
        except NameError:
            raise VoltronException(f'Error building sector from pattern, Value argument must be missed for "{name}"')
        except Exception as err:
            raise VoltronException(f'Unknown exception parsing selector pattern: "{err}"')
    _logger.debug(f'Parsed selector pattern "{pattern_data}"')
    return pattern_data


def find_element(selector, context=None,
                 bypass_exceptions=(NoSuchElementException, StaleElementReferenceException, WebDriverException),
                 timeout=15):
    context = context if context else get_driver()
    (by, val) = parse_selector(selector)
    try:
        element = context.find_element(by=by, value=val)
    except InvalidSelectorException as e:
        raise GeneralException(e.msg)
    except (NoSuchElementException, WebDriverException):
        return wait_for_result(lambda: context.find_element(by=by, value=val),
                               name=f'Waiting for web element to exist by selector {selector}',
                               bypass_exceptions=bypass_exceptions,
                               timeout=timeout
                               )
    return element


def find_elements(selector, context=None,
                  bypass_exceptions=(NoSuchElementException, StaleElementReferenceException, WebDriverException),
                  timeout=15):
    context = context if context else get_driver()
    (by, val) = parse_selector(selector)
    try:
        elements = context.find_elements(by=by, value=val)
    except InvalidSelectorException as e:
        raise VoltronException(e.msg)
    except WebDriverException:
        elements = wait_for_result(lambda: context.find_elements(by=by, value=val),
                                   name=f'Waiting for web elements to exist by selector {selector}',
                                   bypass_exceptions=bypass_exceptions,
                                   timeout=timeout
                                   )
    if not elements:
        elements = wait_for_result(lambda: context.find_elements(by=by, value=val),
                                   name=f'Waiting for web elements to exist by selector {selector}',
                                   bypass_exceptions=bypass_exceptions,
                                   timeout=timeout
                                   )
    return [] if elements is None else elements
