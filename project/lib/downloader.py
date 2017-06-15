import BeautifulSoup
import sys
from selenium import webdriver
import time


class Downloader:
    TEACHING_PORTAL = "https://idp.polito.it/idp/x509mixed-login"

    def __init__(self):
        # ToDo for now only implemented with chrome but constructor need the browser
        self.driver = webdriver.Chrome('./chromedriver')
        self.driver.set_page_load_timeout(10)

    def login(self):
        self.driver.get(self.TEACHING_PORTAL)
        print(self.driver.current_url)
        while self.driver.current_url == self.TEACHING_PORTAL:
            print("Current page: " + self.driver.current_url + " i'm going to sleep")
            time.sleep(2)

        # sleep for page redirection
        time.sleep(2)
        if self.driver.current_url != "https://www.polito.it/intranet/" \
                and self.driver.current_url != "https://idp.polito.it/idp/Authn/X509Mixed/UserPasswordLogin":
            print("Login error url: " + self.driver.current_url)
            self.driver.close()
            sys.exit(-1)

        self.driver.get("https://login.didattica.polito.it/secure/ShibLogin.php")

        return

