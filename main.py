import logging
import ssl
import time
from undetected_chromedriver import Chrome
from LinkedInDriver import run
from selenium_helper.globals import set_driver

# Create a logger
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Use standard library SSL context
ssl._create_default_https_context = ssl._create_stdlib_context


def initialize_driver(retries=3, delay=5):
    for attempt in range(retries):
        try:
            logger.debug(f"Attempt {attempt + 1} to initialize Chrome driver")
            driver = Chrome(user_data_dir="/Users/abhishek.diwate/Library/Application Support/Google/Chrome")
            set_driver(driver)
            return driver
        except Exception as e:
            logger.error(f"Attempt {attempt + 1} failed: {e}", exc_info=True)
            if attempt < retries - 1:
                time.sleep(delay)
            else:
                raise


def main():
    try:
        driver = initialize_driver()
        logger.debug("Running LinkedIn automation")
        run()
    except Exception as e:
        logger.error("An error occurred during the Chrome driver initialization or LinkedIn automation run.",
                     exc_info=True)
    finally:
        if 'driver' in locals():
            logger.debug("Closing the driver")
            driver.quit()


if __name__ == "__main__":
    main()
