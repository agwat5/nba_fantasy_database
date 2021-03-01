#https://m-dendinger19.medium.com/scrape-espn-fantasy-data-with-selenium-4d3b1fdb39f3

import time
from selenium import webdriver
from selenium.common.exceptions import TimeoutException
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.support.ui import WebDriverWait # available since 2.4.0
from selenium.webdriver.support import expected_conditions as EC # available since 2.26.0
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from selenium.webdriver.common.action_chains import ActionChains
from pywebcopy import save_website
from pywebcopy import WebPage
import pywebcopy
from bs4 import BeautifulSoup
import pandas as pd
pywebcopy.config['bypass_robots'] = True
from datetime import datetime
from selenium.webdriver.common.action_chains import ActionChains


#driver saved in \Windows\System32
driver = webdriver.Chrome('chromedriver')

driver.get('https://www.espn.com/');
time.sleep(2)
##Open Initial Log In Location
search_box = driver.find_element_by_id('global-user-trigger')
search_box.click()
time.sleep(2)
print('Open Log In Tab')
##Click on the Log In location
nextbox = driver.find_element_by_xpath("//div[not(contains(@class,'container'))]//a[@data-affiliatename='espn']")
print('success')
print("Element is visible? " + str(nextbox.is_displayed()))
print('waited')
# ActionChains(driver).move_to_element(nextbox).click(nextbox).perform()
nextbox.click()
print('Click Login')
##Switch to iFrame to enter log in credentials
time.sleep(2)
driver.switch_to.frame("disneyid-iframe")
username = driver.find_element_by_xpath("//input[@placeholder='Username or Email Address']")
print('Switching to iFrame')
##Submit Username and Password
time.sleep(2)
username.send_keys('USERNAME')
password = driver.find_element_by_xpath("//input[@placeholder='Password (case sensitive)']")
password.send_keys('PASSWORD')
time.sleep(2)
print('Logging In')
##Submit credentials
button = driver.find_element_by_xpath("//button[@class='btn btn-primary btn-submit ng-isolate-scope']")
button.click()
driver.page_source
##Open Link Page
time.sleep(8)
search_box = driver.find_element_by_id('global-user-trigger')
search_box.click()
print('Going to Fantasy Link')
##Selecting Fantasy League
time.sleep(2)
leaguego = driver.find_element_by_partial_link_text('FANTASY TEAM NAME')
leaguego.click()
print('Entering League')
site = driver.page_source