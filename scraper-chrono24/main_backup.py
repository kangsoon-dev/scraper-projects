from selenium import webdriver
# from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
# from selenium.webdriver.common.keys import Keys
# from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support.expected_conditions import presence_of_element_located
from selenium.common.exceptions import ElementNotInteractableException
from selenium.common.exceptions import ElementClickInterceptedException
from selenium.common.exceptions import NoSuchElementException
from selenium.common.exceptions import StaleElementReferenceException
import pandas as pd
import numpy as np
import time
import bisect
import sys


def next_page(driver):
    try:
        driver.find_element_by_xpath('.//a[@class="paging-next"]').click()
        return False
    # except ElementClickInterceptedException as e1:
    #     driver.find_element_by_xpath('.//button[@class="_3VKU_-kL"]').click()
    #     driver.find_element_by_xpath('.//a[@class="ui_button nav next primary "]').click()
    except NoSuchElementException as e2:  # last page of all reviews
        return True


# def get_url_at_page(url, page):
#     if page > 0:
#         pos = url.find("Reviews-")
#         result = url[:pos + 7] + "-or" + str(page * 5) + url[pos + 7:]
#     else:
#         result = url
#     return result

def decompose_scope(scope):
    box, papers = "Y", "Y"
    for segment in scope.split(","):
        segment = segment.strip().lower()
        if segment.split(" ",1)[0] == "no":
            if segment.split(" ",1)[1] == "original box":
                box = "N"
            elif segment.split(" ",1)[1] == "original papers":
                papers = "N"
    return box, papers

is_deploy_mode = False
get_hot = False

term_list_directory = 'search_terms.csv'
input_rows = pd.read_csv(term_list_directory, index_col=0)
# input_rows = pd.DataFrame([['rolex',0]],columns=['term','done'])
options = webdriver.ChromeOptions()
options.add_argument('--headless')
options.add_argument("--ignore-certificate-errors")
options.add_argument("--incognito")
options.add_experimental_option('excludeSwitches', ['enable-logging'])
driver = webdriver.Chrome(options=options)
driver.set_window_size(1024, 768)
if get_hot:
    driver_item = webdriver.Chrome(options=options)

### clear initial popup button click
base_url = "https://www.chrono24.sg"
page_size = 120
driver.get(base_url)
time.sleep(1)
driver.find_element_by_xpath('.//a[@data-label="accept-button"]').click()
print("click")
time.sleep(1)

for i, row in input_rows.iterrows():
    term = row['term']
    url_template = 'https://www.chrono24.sg/rolex/index-{0}.htm?dosearch=true&pageSize={1}&resultview=list&sortorder=15&query={2}'
    if row['done'] > 0:
        continue
    driver.get(url_template.format(1, page_size, term))
    print("search: " + term)

    isRun = True
    while isRun:
        output_file_name = "{}.csv"
        isRun = False
        columns = ['title', 'movement', 'case_material', 'year', 'condition', 'ref', 'box', 'papers', 'location',
                   'case_diameter', 'price', 'url', 'hot_48']
        try:
            output = pd.read_csv(output_file_name.format(term), index_col=0)
            page = 1
            # if len(output) == 0:
            #     page = 1
            # else:
            #     page = int(output.tail(1)['page']) + 1
        except FileNotFoundError as e:
            output = pd.DataFrame(columns=columns)
            output.to_csv(term + ".csv", index_label='id')
            page = 1

        index_list = list(output.index)
        index_list.sort()

        # get number of pages
        num_items = driver.find_element_by_class_name("h1.m-b-0.text-center").text.split(" ")[2].replace(",", "")
        num_pages = int(np.ceil(int(num_items)/page_size))
        page_list = [i+1 for i in range(num_pages)]

        isStop = False
        while not isStop:
            # expand the review
            print("Page " + str(page))
            time.sleep(1)
            try:
                # container = driver.find_element_by_xpath("//div[@id='wt-watches']")
                # content_list = container.find_elements_by_xpath("./*")
                content_list = driver.find_elements_by_class_name("article-item-container.wt-search-result")

                for j in range(len(content_list[:])):
                    url_segment = content_list[j].get_attribute('outerHTML').split('\n', 2)[1].split('"', 3)[1]
                    # print(url_segment)
                    item_url = base_url + url_segment
                    try:
                        id = int(item_url.split("--id")[1].split(".", 1)[0])
                    except IndexError as e:
                        print(e)
                        print(url_segment)
                    if id not in index_list:
                        content = content_list[j].text.split("\n")
                        # print(content)
                        offset = 0
                        note = ""
                        if content[0] == "TOP":
                            offset = 1
                        if content[0] == "AUCTION":
                            note = "Auction"
                            offset = 1
                        title = content[0+offset]
                        movement = content[2+offset]
                        case_material = content[4+offset]
                        year = content[6+offset]
                        condition = content[8+offset]
                        ref = content[10+offset]
                        scope = content[12+offset]
                        box, papers = decompose_scope(scope)
                        location = content[14+offset]
                        case_diameter = content[16+offset]
                        price = content[17+offset]
                        if get_hot:
                            try:
                                driver_item.get(item_url)
                                hot_48 = driver_item.find_element_by_class_name("m-b-2.clearfix").text.split(" ")[0]
                            except NoSuchElementException as e:
                                hot_48 = 0
                        else:
                            hot_48 = -1
                        new_entry = pd.DataFrame(
                            [[title, movement, case_material, year, condition, ref, box, papers, location, case_diameter,
                              price, item_url, hot_48]],
                            columns=columns, index=[id])
                        new_entry.to_csv(output_file_name.format(term), mode='a', header=False)
                        bisect.insort(index_list, id)

                    # if date_post[-4:-2] == "20" and int(date_post[-4:]) < 2018:
                    #     isStop = True
                    #     break
                if next_page(driver):
                    break
                page += 1
            except StaleElementReferenceException as e:
                print('stale')
                isRun = True
                break
    if is_deploy_mode:
        search_terms.loc[i, 'done'] = len(index_list)
        search_terms.to_csv(term_list_directory)
        print("Completed: " + term)
