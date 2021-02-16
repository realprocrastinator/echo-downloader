from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from exceptions import EchoDownloaderExceptions

# global var section
WAIT_TIME = 120


class WebBrowser(object):
    def __init__(self, browser_type="Chrome", opts=None, credentials=None, display=True):
        driver_opts = Options()
        # This is required to run in the root mode
        driver_opts.add_argument("--no-sandbox")

        if opts:
            for o in opts:
                driver_opts.add_argument(o)

        self._driver = webdriver.Chrome(options=driver_opts)
        self._session = None

    @property
    def web_driver(self):
        return self._driver

    def browse_to(self, url):
        self._driver.get(url)

    # login can be done via cmd line or in the browser
    def login(self, login_url, user_email=None, username=None, mode="cmd"):
        if not self._driver:
            raise EchoDownloaderExceptions("Driver not installed error!")

        res = False

        if mode == "cmd":
            # TODO(Andy): cmd line mode
            print("Feature not implemented yet!")
            res = False
        elif mode == "browser":
            # access the login session
            self._driver.get(login_url)

            # first we need to wait for user inputing email
            print("Please entre the email in format 'name@student.unsw.edu.au'")
            try:
                WebDriverWait(self._driver, WAIT_TIME).until(
                    EC.presence_of_element_located((By.ID, "loginArea")))
            except Exception as e:
                print("Failed to access the login session.")
                print(e)
                self._driver.close()

            print("Welcome to UNSW login session!")

            print("Please type your username and password.")
            try:
                WebDriverWait(self._driver, WAIT_TIME).until(
                    EC.presence_of_element_located((By.XPATH, "//*[@class='course-section-header']")))
            except Exception as e:
                print("Failed to access the syllabus page.")
                self._driver.close()
            print("Ready to retrieve the video info!")

            # success
            res = True

        else:
            print("Invalid login mode.")
            self._driver.close()

        return res


if __name__ == "__main__":
    pass
