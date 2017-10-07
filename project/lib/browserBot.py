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
    download_website = ""
    LOAD_TIMEOUT = 20
    subjects = []
    last_percent_reported = None

    def __init__(self, user, password, saved=False):
        # ToDo for now only implemented with chrome but constructor need the browser
        self.driver = webdriver.Chrome('./chromedriver_win.exe')
        self.driver.set_page_load_timeout(self.LOAD_TIMEOUT)
        self.saved = saved
        self.current_course = None
        if self.saved and os.path.exists('config.json'):
            self.retrieve_user()
        elif self.saved and user and password:
            self.create_user(user, password)
        else:
            self.user = None
            self.password = None

    @property
    def current_course(self):
        return self.current_course

    @current_course.setter
    def set_current_course(course):
        current_course = course

    def create_user(self, user, password, config_name='config.json'):
        user_credential = {'user': user, 'password': password}
        with open(config_name, 'w') as f:
            json.dump(user_credential, f)
        # os.chmod(config_name, S_IREAD)
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

    def get_subject_courses(self):
        try:
            subjects_web_elements = self.secure_find_elements_by_class('policorpolink')

            for subject_web in subjects_web_elements:
                if subject_web.get_attribute('href').find('sviluppo.chiama') != -1:
                    self.subjects.append(Course(subject_web.text, href=subject_web.get_attribute('href')))
        except NoSuchElementException as noElExc:
            print"Connection error"

        return self.subjects

    def get_lessons_page_from_course(self, course):
        self.driver.get(course.href)
        self.driver.get('https://didattica.polito.it/pls/portal30/sviluppo.pagina_corso.main?t=3')
        videolesson_url = self.secure_find_elements_by_class('videoLezLink')
        self.driver.get(videolesson_url[len(videolesson_url)-1].get_attribute('href'))

        return

    def is_valid_didattica_lessons_url(self):
        is_valid = False
        videolessons_url = self.driver.current_url
        videolessons_url_splitted = videolessons_url.split("/")
        url_domain = videolessons_url_splitted[2]
        if url_domain == Course.DIDATTICA_WEBSITE:
            portal_route = videolessons_url_splitted[5].split("?")
            portal = portal_route[0]
            is_valid = (portal == "sviluppo.videolezioni.vis")

        return is_valid

    def is_valid_elearning_lesson_url(self):
        is_valid = False
        videolessons_url = self.driver.current_url
        videolessons_url_splitted = videolessons_url.split("/")
        url_domain = videolessons_url_splitted[2]
        if url_domain == Course.ELEARNING_WEBSITE:
            portal_route = videolessons_url_splitted[5].split("?")
            page = portal_route[0]
            is_valid = (page == "index.php")

        return is_valid
        """//https://elearning.polito.it/main/newscorm/lp_controller.php?cidReq=2018_01OTWOV_0218961&action=view&lp_id=1&isStudentView=true
        return url_domain == self.ELEARNING_WEBSITE and page == "lp_controller.php"
        """

    def get_course_from_current_url(self):
        course = None
        if self.is_valid_didattica_lessons_url():
            course_name = self.secure_find_element_by_class('text-primary').get_attribute('innerText')
            if course_name is not None:
                course = Course(course_name, Course.DIDATTICA_WEBSITE)
        elif self.is_valid_elearning_lesson_url():
            course_name = self.secure_find_element_by_id('learning_path_right_zone').find_element_by_xpath('.//h2').text
            if course_name is not None:
                course = Course(course_name, Course.ELEARNING_WEBSITE);
        return course

    def lessons_website_from_current_url(self):
        website = ''
        if self.is_valid_didattica_lessons_url():
            website = Course.DIDATTICA_WEBSITE
        elif self.is_valid_elearning_lesson_url():
            website = Course.ELEARNING_WEBSITE
        return website

    def download_didattica_lessons(self, course):
        lessons_arguments_web_elements = self.secure_find_elements_by_class('argomentiEspansi')
        lessons_arguments = []
        """Take arguments of lesson from class, concatenate them to put in the title when lesson is downloaded"""
        for lesson_arguments_web_element in lessons_arguments_web_elements:
            lessons_arguments.append(lesson_arguments_web_element.text.replace('.', '').replace('\n', ''))

        lessons = self.driver.find_elements_by_css_selector("#navbar_left_menu .h5 a")
        lessons_links = list(map(lambda l: l.get_attribute('href'), lessons))
        self.download_lessons_with_arguments_and_links(course, lessons_links, lessons_arguments)
        return

    def download_elearning_lessons(self, course):
        lessons_arguments = []
        lessons_data = self.secure_find_elements_by_class('lezioni')[1]
        lessons_arguments_web_elements = lessons_data.find_elements_by_xpath('//ul/ul')
        lessons_links_web_elements = lessons_data.find_elements_by_xpath('.//li/a')
        lessons_links = list(map(lambda l: l.get_attribute('href'), lessons_links_web_elements))
        for i in range(course.start_download-1, course.end_download):
            lessons_arguments.append(self.concat_lesson_arguments(
                lessons_arguments_web_elements[i].find_elements_by_xpath('.//li')))
        self.download_lessons_with_arguments_and_links(course, lessons_links, lessons_arguments)

        return

    @staticmethod
    def concat_lesson_arguments(lesson_arguments_web_element):
        concat_arguments = ''
        for description in lesson_arguments_web_element:
            concat_arguments += '-' + description.text.replace('.', '')
        return concat_arguments

    def download_lessons_with_arguments_and_links(self, course, lessons_links, lessons_arguments):
        if not os.path.exists(course.name):
            os.mkdir(course.name)
        try:
            for i in range(course.start_download, course.end_download + 1):
                self.driver.get(lessons_links[i - 1])
                temp_name = 'Lezione ' if i >= 10 else 'Lezione 0'
                filename = temp_name + str(i) + '-' + lessons_arguments[i - 1].replace('/', '\\') + '.mp4'
                url = self.driver.find_element_by_link_text('Video').get_attribute('href')
                cookies = self.driver.get_cookies()
                self.download_lesson(
                    filename,
                    url,
                    cookies,
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
