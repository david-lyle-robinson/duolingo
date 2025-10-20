#!/usr/bin/python3

# TODO: Add "keep alive" code to do some activity approx once every 3 hrs in between practice sessions

# NOTE: Installing selenium  
#       The driver needs to match the version of chrome installed in the linux VM
#       https://www.youtube.com/watch?v=RBpZ_kUTlqM&ab_channel=NorySoft
# NOTE2: As of chrome v114, a matching chromedriver no longer needs to be manually downloaded and matched.
# Now this is done automatically using "Chrome for Test" mechanism that comes with each version of chrome.
# This is done through the "Selenium Manager" that is built into selenium 4.11.0+


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

    if args.stay_open or args.schedule:
        chrome_options.add_experimental_option("detach", True)
    

    # Print the current time to stdout
    print("\n")
    current_datetime = datetime.datetime.now()
    logger.info("====== START: {0} ======".format(current_datetime))

    # Open the browser
    browser = start_browser_and_login()


    if args.schedule:
        # User has requested specific times to run the practice exercise.  
        logger.debug("Found schedule list: {0}".format(args.schedule))

        for timestring in args.schedule.split(","):
            (hour,minutes) = timestring.split(":")

            # Sunday is special.  Only set if AM. Note that timestring is in 24hr format
            if (int(hour) < 12):
                logger.info("Scheduling sunday {0}".format(timestring))
                schedule.every().sunday.at(timestring).do(do_words_practice_exercise, (browser))

            # Monday is special.  Only set if PM. Note that timestring is in 24hr format
            if (int(hour) >= 12):
                logger.info("Scheduling monday {0}".format(timestring))
                schedule.every().monday.at(timestring).do(do_words_practice_exercise, (browser))

            # All other days, set no matter if AM or PM
            logger.info("Scheduling tuesday {0}".format(timestring))
            schedule.every().tuesday.at(timestring).do(do_words_practice_exercise, (browser))

            logger.info("Scheduling wednesday {0}".format(timestring))
            schedule.every().wednesday.at(timestring).do(do_words_practice_exercise, (browser))

            logger.info("Scheduling thursday {0}".format(timestring))
            schedule.every().thursday.at(timestring).do(do_words_practice_exercise, (browser))

            logger.info("Scheduling friday {0}".format(timestring))
            schedule.every().friday.at(timestring).do(do_words_practice_exercise, (browser))

            logger.info("Scheduling saturday {0}".format(timestring))
            schedule.every().saturday.at(timestring).do(do_words_practice_exercise, (browser))

        # Huge assumption for now: Assume all times are xx:30.  Schedule a keep_alive at every hour, on the hour.
        # Note that if a keep alive happens while doing a practive exercise then bad stuff will happen :(
        logger.info("Scheduling keep-alive routine every hour (schedule.every().hour.at(\":00\").do(practice_hub_keepalive)")
        schedule.every().hour.at(":00").do(practice_hub_keepalive, (browser))
        #schedule.every().hour.at(":20").do(practice_hub_keepalive, (browser))
        #schedule.every().hour.at(":25").do(practice_hub_keepalive, (browser))

        while True:
            # Get the number of seconds until the next job is due
            next_job_seconds = schedule.idle_seconds()
             
            # If there are no more jobs, exit the loop
            if next_job_seconds is None:
                break
            
            # If the next job is in the future, sleep for that amount of time
            if next_job_seconds > 0:
                current_datetime = datetime.datetime.now()
                logger.info("{0}: sleeping for {1}".format(current_datetime, next_job_seconds))
                sleep(next_job_seconds)

            current_datetime = datetime.datetime.now()
            logger.info("{0}: Done sleeping. Checking for scheduled job".format(current_datetime))
            
            # Run any pending jobs that are now due
            schedule.run_pending()

            ##
            ##            # Since the above sleep is many hours... do a 25 minute loop of sleeping every second
            ##            # followed by a check for pending runs just to make sure that the next job was caught
            ##            for i in range(1500):
            ##                sleep(1)
            ##                schedule.run_pending()
            #sleep(5)
            #schedule.run_pending

    else:
        do_words_practice_exercise(browser)



############## Classes and methods ##############

def start_browser_and_login():
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
        do_login(browser)
        logger.info("Login attempt: {0}".format(login_attempts))
        browser.webpage.save_screenshot("login_attempts_{0}.png".format(login_attempts))
        sleep(5)

        current_url = browser.webpage.current_url
        login_attempts += 1

    return(browser)



def practice_hub_keepalive(browser):
    current_datetime = datetime.datetime.now()
    logger.debug("In keepalive: {0}".format(current_datetime))
    practice_hub = browser.webpage.find_elements(By.XPATH, "//a[@data-test='practice-hub-nav']")
    if practice_hub:
        logger.info("Clicking on practice_hub button")
        practice_hub[0].click()
    else:
        logger.info("Trying to keep browser alive, but couldn't find the practive hub button :(")

    

def do_words_practice_exercise(browser):
    logger.debug("In do_words_practice_exercise()")

    if args.random_delay_mins:
        delay_seconds = int(args.random_delay_mins) * 60
        logger.debug("-random_delay_mins option used.  Delaying {0} seconds".format(delay_seconds))
        sleep(randint(0,delay_seconds))
    
    # Rather than looking for the button, how about navigating directly to https://www.duolingo.com/practice-hub/words
    # Or.... look for the following button if the first fails:
    # <a data-test="practice-hub-nav" aria-current="page" class="_2dvyl" href="/practice-hub">
    #   <span class="_22Pme _33YLo p3liX YAEPa _3Dchg">
    #     <div class="_4fxfA"><img class="_101n8" src="https://d35aaqx5ub95lt.cloudfront.net/vendor/5187f6694476a769d4a4e28149867e3e.svg"></div>
    #   <span class="_1AZJt">Practice</span></span>
    # </a>

    # Handle case where browser may have timed out and gone back to the login page
    login_attempts = 0
    current_url = browser.webpage.current_url
    while (current_url == "https://www.duolingo.com/?isLoggingIn=true" and login_attempts < 5):
        logger.info("Current URL: {0}".format(current_url))
        do_login(browser)
        browser.webpage.save_screenshot("login_attempts_{0}.png".format(login_attempts))
        sleep(5)

        current_url = browser.webpage.current_url
        login_attempts += 1


    new_url = "https://www.duolingo.com/practice-hub/words"
    logger.info("New URL: {0}".format(current_url))
    browser.webpage.get(new_url)
    sleep(10)


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
        

def do_login(browser):
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
        sleep(3)

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
