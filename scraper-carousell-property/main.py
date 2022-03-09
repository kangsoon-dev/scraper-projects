from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
# from selenium.webdriver.common.keys import Keys
# from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support.expected_conditions import presence_of_element_located
from selenium.common.exceptions import ElementNotInteractableException
from selenium.common.exceptions import ElementClickInterceptedException
from selenium.common.exceptions import NoSuchElementException
from selenium.common.exceptions import StaleElementReferenceException
import pandas as pd
import time
import sys

# def next_page(driver):
#     try:
#         driver.find_element_by_xpath('.//a[@class="ui_button nav next primary "]').click()
#         return False
#     except ElementClickInterceptedException as e1:
#         driver.find_element_by_xpath('.//button[@class="_3VKU_-kL"]').click()
#         driver.find_element_by_xpath('.//a[@class="ui_button nav next primary "]').click()
#     except NoSuchElementException as e2: # last page of all reviews
#         return True
#
# def get_url_at_page(url, page):
#     if page > 0:
#         pos = url.find("Reviews-")
#         result = url[:pos + 7] + "-or" + str(page * 5) + url[pos + 7:]
#     else:
#         result = url
#     return result

def is_post(y):
    if y.split('/')[3] == 'p':
        return True
    return False

search_url = "https://www.carousell.sg/categories/property-102/housing-for-sale-230/hdb-1583/?sort_by=time_created%2Cdescending"
load_pages = 25
options = Options()
options.page_load_strategy = 'eager'
driver = webdriver.Chrome(options=options)
driver.get(search_url)
for x in range(load_pages):
    print("load" + str(x))
    isLogin = True
    while isLogin:
        load_more_button = driver.find_elements_by_tag_name("button")[-1]
        if load_more_button.text == "Load more":
            try:
                load_more_button.click()
            except ElementClickInterceptedException as e:
                time.sleep(1)
                load_more_button.click()
            isLogin = False
        else:
            time.sleep(0.5)
    time.sleep(0.3)
href_list = [y.rsplit("/",1)[0] for y in [x.get_attribute("href") for x in driver.find_elements_by_tag_name("a")] if is_post(y)]
print("Total Listings: " + str(len(href_list)))
driver.close()

columns = ['Features', 'Tenure (Years)', 'Level', 'Furnishing', 'Type', 'Postal Code', 'Estate', 'Street Name', 'Full Name', 'Agency Name', 'Estate Agent License Number', 'CEA Registration Number', 'Mobile Number', 'Meet the seller','Description', 'url']
template = pd.DataFrame(columns=columns,index=[])
template.to_csv("carousell_listings.csv",index=False)
options.add_argument('--headless')
driver = webdriver.Chrome(options=options)

for i, url in enumerate(href_list):
    driver.get(url)
    new_entry = pd.DataFrame([], columns=columns)
    text_section = driver.find_elements_by_tag_name("section")
    if "".join(text_section[0].text)[:5] == "Share":
        desc_section = [x.text for x in text_section[3].find_elements_by_tag_name("p")]
        desc_section = desc_section[desc_section.index("Description")+1:desc_section.index("Location")]
    else:
        desc_section = [x.text for x in text_section[0].find_elements_by_tag_name("p")]
        desc_section = desc_section[:desc_section.index("Location")]
    item_list = [x.text for x in text_section]
    split_item_list = []
    for x in item_list:
        split_item_list += x.split('\n')
    # print(split_item_list)
    for y in columns:
        if y in split_item_list:
            new_entry.at[0,y] = split_item_list[split_item_list.index(y)+1]
        else:
            new_entry.at[0,y] = ""
    new_entry.at[0,'url'] = url
    new_entry.at[0,'Description'] = "".join(desc_section)
    # print(new_entry)
    new_entry.to_csv("carousell_listings.csv", mode='a', header=False, index=False)
    if i%10 == 0:
        print("Progress: "+str(i)+"/"+str(len(href_list)))
    continue




#
# while isRun:
#     isRun = False
#     columns = ['page', 'user', 'country', 'date_post', 'date_stay', 'rating', 'title', 'review_text', 'trip_type',
#                'helpful']
#     try:
#         reviews = pd.read_csv("reviews_" + hotel_name + ".csv", index_col=False)
#         if len(reviews) == 0:
#             page = 1
#         else:
#             page = int(reviews.tail(1)['page']) + 1
#     except FileNotFoundError as e:
#         reviews = pd.DataFrame(columns=columns)
#         reviews.to_csv("reviews_" + hotel_name + ".csv", index=False)
#         page = 0
#
#     driver.get(get_url_at_page(url, page))
#     # change the value inside the range to save more or less reviews
#     isStop = False
#     while not isStop:
#         # expand the review
#         time.sleep(0.6)
#         try:
#             isExpand = True
#             while isExpand:
#                 try:
#                     driver.find_element_by_xpath(".//div[contains(@data-test-target, 'expand-review')]").click()
#                     isExpand = False
#                 except ElementNotInteractableException as e1:
#                     time.sleep(0.3)
#                 except NoSuchElementException as e2:
#                     next_page(driver)
#                     isExpand = False
#             container = driver.find_elements_by_xpath("//div[@data-reviewid]")
#             dates = driver.find_elements_by_xpath(".//div[@class='_2fxQ4TOx']")
#             review_info = driver.find_elements_by_xpath(".//div[@class='_1EpRX7o3']")
#
#             for j in range(len(container)):
#                 user = \
#                     dates[j].find_element_by_xpath(".//a[contains(@class, 'ui_header_link _1r_My98y')]").get_attribute(
#                         "href").split("/")[-1]
#                 if len(review_info[j].find_elements(By.XPATH, ".//span[contains(@class, '_1TuWwpYf')]")) > 0:
#                     country = review_info[j].find_element_by_xpath(".//span[contains(@class, '_1TuWwpYf')]").text
#                 else:
#                     country = "nil"
#                 rating = container[j].find_element_by_xpath(
#                     ".//span[contains(@class, 'ui_bubble_rating bubble_')]").get_attribute(
#                     "class").split("_")[3]
#                 title = container[j].find_element_by_xpath(".//div[contains(@data-test-target, 'review-title')]").text
#                 review_text = container[j].find_element_by_xpath(".//q[@class='IRsGHoPm']").text.replace("\n", "  ")
#                 date_post = " ".join(dates[j].text.split(" ")[-2:])
#                 if len(container[j].find_elements(By.XPATH, ".//span[contains(@class, '_34Xs-BQm')]")) > 0:
#                     date_stay = \
#                         container[j].find_element_by_xpath(".//span[contains(@class, '_34Xs-BQm')]").text.split(":")[
#                             1].strip()
#                 else:
#                     date_stay = "nil"
#                 if len(container[j].find_elements(By.XPATH, ".//span[contains(@class, '_2bVY3aT5')]")) > 0:
#                     trip_type = \
#                         container[j].find_element_by_xpath(".//span[contains(@class, '_2bVY3aT5')]").text.split(":")[
#                             1].strip()
#                 else:
#                     trip_type = "nil"
#                 if len(container[j].find_elements(By.XPATH, ".//span[contains(@class, '_3kbymg8R _2o1bmw1O')]")) > 0:
#                     helpful = \
#                         container[j].find_element_by_xpath(
#                             ".//span[contains(@class, '_3kbymg8R _2o1bmw1O')]").text.split(
#                             ' ')[0]
#                 else:
#                     helpful = 0
#                 new_entry = pd.DataFrame(
#                     [[page, user, country, date_post, date_stay, rating, title, review_text, trip_type, helpful]],
#                     columns=columns)
#                 # print(new_entry)
#                 if not (date_post[-4:-2] == "20" and int(date_post[-4:]) < 2018):
#                     new_entry.to_csv("reviews_" + hotel_name + ".csv", mode='a', header=False, index=False)
#                 if date_post[-4:-2] == "20" and int(date_post[-4:]) < 2018:
#                     isStop = True
#                     break
#             if next_page(driver):
#                 break
#             page += 1
#         except StaleElementReferenceException as e:
#             print('stale')
#             isRun = True
#             break
# hotels.loc[i, 'done'] = len(pd.read_csv("reviews_" + hotel_name + ".csv"))
# hotels.to_csv('hotels.csv')
