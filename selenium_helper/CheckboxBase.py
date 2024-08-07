from selenium_helper.ComponentBase import ComponentBase
from selenium_helper.globals import VoltronException


class CheckBoxBase(ComponentBase):
    _input = 'xpath=.//input'

    @property
    def value(self):
        self.scroll_to_we()
        we = self._find_element_by_selector(selector=self._input)
        if we:
            value = we.is_selected()
        else:
            raise VoltronException('Cannot get checkbox value')
        if value:
            return True
        return False

    @value.setter
    def value(self, value):
        if not isinstance(value, bool):
            raise VoltronException('CheckBox value should be BOOL type (True/False). Got: "%s"' % value)

        if self.value != value:
            if self.is_enabled():
                self._logger.debug(
                    f'*** User has set "{value}" on CheckBox. Call of "{self.__class__.__name__}"'
                )
                self.click()
            else:
                raise VoltronException('CheckBox is disabled so can\'t be clicked')