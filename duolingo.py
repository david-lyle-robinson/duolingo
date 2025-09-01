#!/usr/bin/python3


# NOTE: Installing selenium  
#       The driver needs to match the version of chrome installed in the linux VM
#       https://www.youtube.com/watch?v=RBpZ_kUTlqM&ab_channel=NorySoft
# NOTE2: As of chrome v114, a matching chromedriver no longer needs to be manually downloaded and matched.
# Now this is done automatically using "Chrome for Test" mechanism that comes with each version of chrome.
# This is done through the "Selenium Manager" that is build in selenium 4.11.0+


from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import Select
from selenium.webdriver.common.keys import Keys
#from selenium.webdriver.chrome.options import Options
import os
import schedule
from time import sleep
from random import randint
from random import random
import datetime
import argparse
import logging
import re
import csv

from collections import OrderedDict


################### MAIN ##################
def main():
    global args
    global logger   
    global browser
    global chrome_service
    global chrome_options


    ### ARG HANDLING ###
    parser = argparse.ArgumentParser(allow_abbrev=True, description='Script Description')
    parser.add_argument('-schedule', nargs='?', default="", help='Schedule hours of the day to run.  Example:\"00:24,13:16,23:55\"')
    parser.add_argument('-random_delay_mins', default=0, help='Delay start from 0 to this maximum minutes. Example: 12: Delay from 0 to 12 minute before starting')
    parser.add_argument('-headless', action='store_true', help='Do not show the browser gui')
    parser.add_argument('-stay_open', '-detach', dest="stay_open", action='store_true', help='Keep the browser gui open')
    parser.add_argument('-debug', action='store_true', help='Display debug messages')
    args = parser.parse_args()

    ### LOG HANDLING -- Only dump log data to the xterm ###
    LOG_FORMAT = ("%(levelname)s: %(message)s")
    LOG_DEBUG_FORMAT = ("%(levelname)s: %(module)s:%(lineno)s %(funcName)s: %(message)s")
    LOG_LEVEL = logging.INFO
    if args.debug:
        LOG_LEVEL = logging.DEBUG
        LOG_FORMAT = LOG_DEBUG_FORMAT
    
    logging.basicConfig(level=LOG_LEVEL, format=LOG_FORMAT)
    logger = logging.getLogger()
    
    if args.stay_open and args.headless:
        logger.error(" -detach (-stay_open) and -headless are mutually exclusive options.  Please choose one.")
        exit()

    if args.random_delay_mins:
        delay_seconds = int(args.random_delay_mins) * 60
        sleep(randint(0,delay_seconds))

    # Using Chrome to access web
    #chrome_options = Options()
    chrome_service = Service()
    chrome_options = webdriver.ChromeOptions()
    chrome_options.add_argument("--disable-cache") 
    #options = webdriver.ChromeOptions()
    #options.add_argument('--headless')
    #options.add_argument('--no-sandbox')
    #options.add_argument('--disable-dev-shm-usage')

    #chrome_options.page_load_strategy = 'eager'
    if args.headless:
        chrome_options.add_argument('headless')
        #chrome_options.add_argument('start-maximized')
        chrome_options.add_argument('--window-size=1920,1080')
        # User agent strings documented here: https://www.whatismybrowser.com/guides/the-latest-user-agent/chrome
        custom_user_agent = "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/139.0.0.0 Safari/537.36"
        chrome_options.add_argument(f'user-agent={custom_user_agent}')
    if args.stay_open:
        chrome_options.add_experimental_option("detach", True)
    

    # Open the website


    if args.schedule != "":
        logger.debug("Found schedule list: {0}".format(args.schedule))
        #schedule.every().hour.do(check_sites_wrapper, browser=browser)
        # schedule.every().day.at("23:55:00").do(check_sites_wrapper, browser=browser)

        for timestring in args.schedule.split(","):
            logger.info("Scheduling {0}".format(timestring), flush=True)
            #schedule.every().day.at(timestring).do(check_sites_wrapper)
            schedule.every().day.at(timestring).do(check_and_book)
            
        while True:
            # Checks whether a scheduled task
            # is pending to run or not
            schedule.run_pending()
            sleep(1)

    else:

        # Get the current date and time
        current_datetime = datetime.datetime.now()

        # Print the datetime object
        #print(current_datetime)
        print("\n")
        logger.info("====== START: {0} ======".format(current_datetime))

        open_url = "https://www.duolingo.com/?isLoggingIn=true"

        logger.info("opening {0}".format(open_url))
        browser = Browser(chrome_options, chrome_service, open_url)
        logger.debug("Browser object is created")
        
        have_account_button = browser.webpage.find_element(By.XPATH, "//button[@data-test='have-account']")
        have_account_button.click()
        sleep(2)


        current_url = browser.webpage.current_url
        login_attempts = 0
        while (current_url == "https://www.duolingo.com/?isLoggingIn=true" and login_attempts < 5):
            logger.debug("Current URL: {0}".format(current_url))
            # When re-attempting, reload just to be sure we're fully reset
            #if login_attempts > 0:
            #    browser.webpage = browser.webpage.get(current_url)
            do_login()
            browser.webpage.save_screenshot("login_attempts_{0}.png".format(login_attempts))
            sleep(5)
            current_url = browser.webpage.current_url
            login_attempts += 1

        logger.info("New URL: {0}".format(current_url))

        #practice_hub = browser.webpage.find_element(By.XPATH, "//button[@data-test='practice-hub-nav']")
        #practice_hub.click()
        new_url = "https://www.duolingo.com/practice-hub"
        browser.webpage.get(new_url)

        words_practice = browser.webpage.find_elements(By.XPATH, "//button[@data-test='practice-hub-collection-button']//span[contains(text(), 'Words')]")
        while (not words_practice):
            sleep(2)
            words_practice = browser.webpage.find_elements(By.XPATH, "//button[@data-test='practice-hub-collection-button']//span[contains(text(), 'Words')]")

        words_practice[0].click()


        # Now build vocabulary
        #alpha list mode
        #recently_learned = browser.webpage.find_element(By.XPATH, "//span[contains(text(), 'RECENTLY LEARNED')]")
        #<button aria-controls="web-ui6" aria-haspopup="listbox" class="_33q67 _2bftX" type="button"></button>
        #recently_learned = browser.webpage.find_element(By.XPATH, "//button[@aria-haspopup='listbox' and @type='button']")
        #recently_learned = browser.webpage.find_element(By.XPATH, "//button[@type='button']")
        #recently_learned.click()

        sleep(3)
        start_button = browser.webpage.find_element(By.XPATH, "//button//span[contains(text(), 'Start')]")
        start_button.click()

        sleep(8)

        continue_button = browser.webpage.find_element(By.XPATH, "//button[@data-test='player-next']//span[contains(text(), 'Continue')]")
        continue_button.click()


        logger.debug("\nEnglish words to Spanish words")
        english_words = browser.webpage.find_elements(By.XPATH, "//button[@lang='en' and contains(@data-test,'challenge-tap-token') and @aria-disabled='false']//span[@data-test='challenge-tap-token-text']")
        english_words_to_spanish_words(english_words)
        current_datetime = datetime.datetime.now()
        logger.info("{0}: Finished English words to Spanish words".format(current_datetime))
        sleep(4)

        # Press Continue
        continue_button = browser.webpage.find_element(By.XPATH, "//button[@data-test='player-next']")
        continue_button.click()
        sleep(2)

        logger.debug("\nSpanish audio to English words")
        spanish_words = browser.webpage.find_elements(By.XPATH, "//button[@lang='es' and contains(@data-test,'challenge-tap-token') and @aria-disabled='false']")
        spanish_audio_to_english_word2(spanish_words)
        current_datetime = datetime.datetime.now()
        logger.info("{0}: Finished Spanish audio to English words".format(current_datetime))
        sleep(4)

        # Press Continue
        continue_button = browser.webpage.find_element(By.XPATH, "//button[@data-test='player-next' and @aria-disabled='false']")
        continue_button.click()
        sleep(2)

        logger.debug("\nEnglish words to Spanish words")
        english_words = browser.webpage.find_elements(By.XPATH, "//button[@lang='en' and contains(@data-test,'challenge-tap-token') and @aria-disabled='false']//span[@data-test='challenge-tap-token-text']")
        english_words_to_spanish_words(english_words)
        current_datetime = datetime.datetime.now()
        logger.info("{0}: Finished English words to Spanish words".format(current_datetime))


        # Press continue as many times as is necessary
        continue_button = browser.webpage.find_elements(By.XPATH, "//button[@data-test='player-next' and @aria-disabled='false']")
        while (continue_button):
            continue_button[0].click()
            sleep(3)
            continue_button = browser.webpage.find_elements(By.XPATH, "//button[@data-test='player-next' and @aria-disabled='false']")
        


############## Classes and methods ##############
def test_if_element_exists(elem, search_method, criteria):
    try:
        e = elem.find_element(search_method, criteria)
        return(True)
    except:
        return(False)

def do_login():
    login_field = browser.webpage.find_element(By.XPATH, "//input[@data-test='email-input']")
    login_field.clear()
    login_field.send_keys("david@robinsonhome.net")
    sleep(2)
    password_field = browser.webpage.find_element(By.XPATH, "//input[@data-test='password-input']")
    password_field.clear()
    sleep(0.5)
    password_field.send_keys("bjm")
    sleep(random())
    password_field.send_keys("jm")
    sleep(random())
    password_field.send_keys("nk")
    sleep(2)

    login_button = browser.webpage.find_element(By.XPATH, "//button[@data-test='register-button']")
    login_button.click()


def english_words_to_spanish_words(english_words):
    if not english_words:
        logger.debug("english_words_to_spanish_words activity completed")
        return
        
    for en_word in english_words:
        #print("english_word element = {0}".format(en_word.get_attribute('outerHTML'))) 
        spanish_words = browser.webpage.find_elements(By.XPATH, "//button[@lang='es' and contains(@data-test,'challenge-tap-token') and @aria-disabled='false']//span[@data-test='challenge-tap-token-text']")
        for es_word in spanish_words:
            # For each attempt in the spanish list, you need to reclick the first english word
            logger.debug("Clicking english word: {0}".format(en_word.text))
            en_word.click()
            sleep(1)

            spanish_word = es_word.text
            logger.debug("Clicking spanish word: {0}".format(spanish_word))
            es_word.click()
            sleep(3)

            # test to see if this word is now disabled
            #<button class="_2wryV _3fmUm _2V6ug _1ursp _7jW2t notranslate _3ZtW_ _2O7Ua _3U5_i _3Ymqr" dir="ltr" lang="es" translate="no" data-test="navidad-challenge-tap-token" aria-disabled="true">
            # test to see if this word is now disabled
            test_pattern = "//button[@lang='es' and @data-test='{0}-challenge-tap-token' and @aria-disabled='true']".format(spanish_word)
            logger.debug("disabled test_pattern = {0}".format(test_pattern))
            test_es_word = browser.webpage.find_elements(By.XPATH, test_pattern)

            if (test_es_word):
                for word in test_es_word:
                    logger.debug("Disabled Word: {0}".format(word.get_attribute('data-test')))
                break
            sleep(2)
        sleep(2)

    english_words = browser.webpage.find_elements(By.XPATH, "//button[@lang='en' and contains(@data-test,'challenge-tap-token') and @aria-disabled='false']//span[@data-test='challenge-tap-token-text']")
    english_words_to_spanish_words(english_words)



def spanish_audio_to_english_word2(spanish_audio_clips):
    if not spanish_audio_clips:
        logger.debug("spanish_audio_to_english activity completed")
        return

    es_audio = spanish_audio_clips.pop()
    challenge_tap_token = es_audio.get_attribute('data-test')
    logger.debug("Clicking spanish audio: {0}".format(challenge_tap_token))
    es_audio.click()

    # NOTE: challenge_tap_token often has apostrophes.  Therefore using escaped double quotes around it to allow single quote marks in the variable
    english_word = browser.webpage.find_element(By.XPATH, "//button[@lang='en' and @data-test=\"{0}\" and @aria-disabled='false']".format(challenge_tap_token))
    logger.debug("Clicking matching english word: {0}".format(challenge_tap_token))
    english_word.click()
    sleep(5)

    spanish_audio_clips = browser.webpage.find_elements(By.XPATH, "//button[@lang='es' and contains(@data-test,'challenge-tap-token') and @aria-disabled='false']")
    spanish_audio_to_english_word2(spanish_audio_clips)



def spanish_audio_to_english_word(spanish_audio_clips):
    if not spanish_audio_clips:
        logger.debug("spanish_audio_to_english activity completed")
        return

    es_audio = spanish_audio_clips.pop()
    #for es_audio in spanish_audio_clips:
    #print("spanish_word element = {0}".format(es_audio.get_attribute('outerHTML'))) 

    # ENGLISH TRANSLATION:
    # <button class="_3fmUm _2V6ug _1ursp _7jW2t notranslate _3ZtW_ _2O7Ua _3U5_i _3Ymqr" dir="ltr" lang="en" translate="no" data-test="Christmas-challenge-tap-token" aria-disabled="false"><span class="_12ozk"></span><span class="_231NG b69xA"><span data-test="challenge-tap-token-text">Christmas</span>
    #english_words = browser.webpage.find_elements(By.XPATH, "//button[@lang='en' and contains(@data-test,'challenge-tap-token') and @aria-disabled='false']//span[@data-test='challenge-tap-token-text']")
    english_words = browser.webpage.find_elements(By.XPATH, "//button[@lang='en' and contains(@data-test,'challenge-tap-token') and @aria-disabled='false']")
    for en_word in english_words:
        saved_data_test = en_word.get_attribute('data-test')
        logger.debug("saved data-test: {0}".format(saved_data_test))

        # For each attempt in the english list, you need to reclick the current spanish word
        logger.debug("Clicking spanish word: {0}".format(es_audio.text))
        es_audio.click()
        #print("es_audio: {0}".format(es_audio.get_attribute('outerHTML')))
        sleep(1)

        logger.debug("Clicking english word: {0}".format(saved_data_test))
        #print("\ten_word: {0}".format(en_word.get_attribute('outerHTML')))
        en_word.click()

        sleep(3)

        check_success = browser.webpage.find_elements(By.XPATH, "//button[@lang='en' and @data-test='{0}']".format(saved_data_test))

        if (check_success):
            logger.debug("Found {0} in the list. Continue")
            continue
        else:
            logger.debug("{0} NOT FOUND in the list. Restart looping")
            break

    spanish_audio_clips = browser.webpage.find_elements(By.XPATH, "//button[@lang='es' and contains(@data-test,'challenge-tap-token') and @aria-disabled='false']")
    spanish_audio_to_english_word(spanish_audio_clips)


class Browser:
    def __init__(self, options, service, url):
        self.options = options
        self.service = service
        self.webpage = webdriver.Chrome(options=self.options, service=self.service)
        self.webpage.get(url)

    def new_webpage(self, url):
        self.webpage.get(url)

    def wait_till_id_visible(self, id):
        try:
            e = WebDriverWait(self.webpage, 5).until(EC.visibility_of_element_located((By.ID, id)))
            return True
        except:
            return False

    def wait_till_element_visible(self, by, element):
        if (by == "XPATH"):
            search_by = By.XPATH
        elif (by == "ID"):
            search_by = By.ID
        elif (by == "CLASS_NAME"):
            search_by = By.CLASS_NAME
        
        try:
            e = WebDriverWait(self.webpage, 5).until(EC.visibility_of_element_located((search_by, element)))
            return True
        except:
            return False


    def wait_till_element_is_clickable(self, element):
        try:
            e = WebDriverWait(self.webpage, 5).until(EC.element_to_be_clickable((By.ID, element)))
            return True
        except:
            return False
        





            

if __name__ == "__main__":
    main()
