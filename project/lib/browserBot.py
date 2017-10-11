from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from tqdm import tqdm
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
from .course import Course
import sys
import os
import time
import requests
import json
from stat import S_IREAD



class BrowserBot:
    LOAD_TIMEOUT = 20
    subjects = []
    last_percent_reported = None

    def __init__(self, user, password, saved=False):
        self.driver = webdriver.Chrome('./chromedriver')
        self.driver.set_page_load_timeout(self.LOAD_TIMEOUT)
        self.saved = saved
        if self.saved and os.path.exists('config.json'):
            self.retrieve_user()
        elif self.saved and user and password:
            self.create_user(user, password)
        else:
            self.user = None
            self.password = None

    def create_user(self, user, password, config_name='config.json'):
        user_credential = {'user': user, 'password': password}
        with open(config_name, 'w') as f:
            json.dump(user_credential, f)
        os.chmod(config_name, S_IREAD)
        self.user = user
        self.password = password

    def retrieve_user(self, config_name='config.json'):
        with open(config_name) as f:
            user_credential = json.load(f)
        self.user = user_credential['user']
        self.password = user_credential['password']

    def wait_page_loaded(self, delay, selector, type='id'):
        """WebDriver will wait until page is ready
        Args:
            delay (int): acceptable delay of loading
            type (str): is a string that could be "class", either "id"
            selector (str): name of class or id
        Returns:
            bool: The return value.True if page is ready, False otherwise
        """
        try:
            if type == 'id':
                WebDriverWait(self.driver, delay).until(EC.presence_of_element_located((By.ID, selector)))
            elif type == 'class':
                WebDriverWait(self.driver, delay).until(EC.presence_of_element_located((By.CLASS_NAME, selector)))
            else:
                raise ValueError
        except TimeoutException:
            print "Loading took too much time! Cannot reach the website"
            return False
        return True

    def secure_find_element_by_id(self, id_name):
        if not self.wait_page_loaded(self.LOAD_TIMEOUT, id_name, 'id'):
            print "Terminating..."
            sys.exit(-1)

        return self.driver.find_element_by_id(id_name)

    def secure_find_element_by_class(self, class_name):
        if not self.wait_page_loaded(self.LOAD_TIMEOUT, class_name, 'class'):
            print "Terminating..."
            sys.exit(-1)

        return self.driver.find_element_by_class_name(class_name)

    def secure_find_elements_by_class(self, class_name):
        if not self.wait_page_loaded(self.LOAD_TIMEOUT, class_name, 'class'):
            print "Terminating..."
            sys.exit(-1)

        return self.driver.find_elements_by_class_name(class_name)

    def login(self):
        portal = 'https://idp.polito.it/idp/x509mixed-login'

        self.driver.get(portal)
        # fix for timeout exception for retry
        while self.driver.current_url == portal:
            time.sleep(2)

            if self.saved and self.user and self.password:
                self.secure_find_element_by_id('j_username').send_keys(self.user)
                self.secure_find_element_by_id('j_password').send_keys(self.password)
                self.secure_find_element_by_class('form-button').click()

        if self.driver.current_url != 'https://www.polito.it/intranet/' \
                and self.driver.current_url != "https://idp.polito.it/idp/Authn/X509Mixed/UserPasswordLogin":
            print("Login error url: " + self.driver.current_url)
            self.driver.close()
            sys.exit(-1)
        self.secure_find_element_by_id('corpo')
        self.driver.get('https://login.didattica.polito.it/secure/ShibLogin.php')
        return

    def get_subject(self):
        try:
            subjects_web_elements = self.secure_find_elements_by_class('policorpolink')

            for subject_web in subjects_web_elements:
                if subject_web.get_attribute('href').find('sviluppo.chiama') != -1:
                    self.subjects.append(Course(subject_web.text, subject_web.get_attribute('href')))
        except NoSuchElementException as noElExc:
            print"Connection error"

        return self.subjects

    def get_lessons_from_course(self, course, start, end):
        self.driver.get(course.href)
        self.driver.get('https://didattica.polito.it/pls/portal30/sviluppo.pagina_corso.main?t=3')
        self.secure_find_element_by_class('videoLezLink').click()

        lesson_titles = self.secure_find_elements_by_class('argomentiEspansi')
        l_t = []
        for lesson_title in lesson_titles:
            tot_description = ''
            for description in lesson_title.find_elements_by_class_name("argoLink"):
                tot_description += '-' + description.get_attribute('text').replace('.', '')
            l_t.append(tot_description)

        lessons = self.driver.find_elements_by_css_selector("#navbar_left_menu .h5 a")
        lessons_link = list(map(lambda l: l.get_attribute('href'), lessons))
        if not os.path.exists(course.name):
                os.mkdir(course.name)

        try:
            for i in range(start, end+1):
                self.driver.get(lessons_link[i-1])
                url = self.driver.find_element_by_link_text('Video').get_attribute('href')
                temp_name = 'Lezione ' if i >= 10 else 'Lezione 0'
                self.download_lesson(
                    temp_name + str(i) + '-' + l_t[i-1].replace('/', '\\') + '.mp4',
                    self.driver.find_element_by_link_text('Video').get_attribute('href'),
                    self.driver.get_cookies(),
                    data_root=course.name
                )
        except IndexError:
            print "Tutte le lezioni sono state scaricate"
        return

    @staticmethod
    def download_lesson(filename, url, cookies, force=False, data_root='.'):
        """Download a file if not present, and make sure it's the right size.
        """
        print('Attempting to download:' + filename)

        download_cookies = {}
        for cookie in cookies:
            download_cookies[cookie["name"]] = cookie["value"]

        r = requests.get(url, cookies=download_cookies, stream=True)
        file_size = int(r.headers.get('content-length'))
        complete_name = (data_root + '/' + filename)
        if force or not os.path.exists(complete_name):
            with open(complete_name, 'wb') as f:
                print "Downloading " + filename
                for chunk in tqdm(r.iter_content(chunk_size=1024), total=file_size/1024, unit='KB'):
                    if chunk:   # filter out keep-alive new chunks
                        f.write(chunk)
                        f.flush()
                print('\nDownload Complete!')
        stat_info = os.stat(complete_name)
        if stat_info.st_size == file_size:
            print('Trovato e verificato', filename)
        else:
            raise Exception(
                'Verifica fallita ' + filename + ' controllare manualmente!')
        return filename
