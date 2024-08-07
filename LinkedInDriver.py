from selenium.webdriver import Keys

from Linkedin.LinkedIn import LinkedIn


def run():
    linkedin = LinkedIn()
    linkedin.search.value = "Hiring React Js"
    linkedin.search.send_keys(Keys.ENTER)
