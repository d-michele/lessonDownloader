from lib import BrowserBot
from selenium.common.exceptions import TimeoutException
from lib import Course
import sys
import os
import getpass


def main():
    usr = None
    passwd = None
    saved = False
    try:
        if sys.argv[1] == '-s':
            print "login memorizzato\n"
            saved = True
            if not os.path.exists('config.json'):
                raw_user = raw_input('inserire username\n')
                print 'inserire password\n'
                raw_password = getpass.getpass()
                try:
                    usr = str(raw_user)
                    passwd = str(raw_password)
                except ValueError:
                    print ("Username e password non valida\n")
        else:
            print 'argomento non esistente\n'
            sys.exit(1)

    except IndexError:
        print "Login sul sito\n"

    browser = BrowserBot(usr, passwd, saved)

    browser = timeout_login(browser)

    lesson_menu(browser)


def lesson_menu(browser):
    subjects = browser.get_subject()

    for i in range(1, len(subjects)):
        print("{} - {}".format(i, subjects[i-1]))
    custom_lesson_choose = i+1
    print ("{} scarica lezioni di una qualsiasi materia".format(custom_lesson_choose))
    print ("0 - Esci")

    while True:
        try:
            choose = raw_input("Scegliere il numero della materia da cui scaricare le lezioni ")
            choose = int(choose)
            #choose = 5
            if choose == 0:
                sys.exit(0)

            if choose == custom_lesson_choose:
                custom_lesson_download(browser)
            else:
                chosed_lesson = subjects[choose-1]
                define_download_range(chosed_lesson)

                browser.get_lessons_from_course(chosed_lesson)
                break
        except IndexError:
            print ("Materia non esistente")
        except ValueError:
            print ("Scelta non valida")
    return

def custom_lesson_download(browser):
    while True:
        raw_input("Navigare fino alla pagina delle videolezioni e premere un tasto")
        selected_course = browser.get_course_from_current_url()
        if selected_course is not None:
            break

    define_download_range(selected_course)
    browser.download_didattica_lesson(selected_course)
    
    return

def define_download_range(course):
    try:
        start = raw_input("vuoi scaricare lezioni dalla ")
        course.start_download = (int(start))
        end = raw_input("alla ")
        course.end_download = (int(end))

        if start < 1 or end < 1:
            raise ValueError
    except ValueError:
        print ("Scelta non valida")

    return

def timeout_login(browser):
    i = 0
    while True:
        try:
            browser.login()
            break
        except TimeoutException:
            if i >= 3:
                sys.exit(1)
            i += 1
    return browser

if __name__ == '__main__':
    main()