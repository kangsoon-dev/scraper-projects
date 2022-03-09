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
from concurrent.futures import ThreadPoolExecutor
import pandas as pd
import numpy as np
import threading
from tqdm import tqdm
import requests
from bs4 import BeautifulSoup
import lxml

global is_deploy_mode
global threads
global page_size
global base_url
global term_list_directory
global url_template
global output_file_name_template
global columns
is_deploy_mode = True
threads = 4
page_size = 120
base_url = "https://www.chrono24.sg"
term_list_directory = 'search_terms.csv'
url_template = 'https://www.chrono24.sg/rolex/index-{0}.htm?dosearch=true&pageSize={1}&resultview=list&sortorder=15&query={2}'
output_file_name_template = "{}.csv"
columns = ['title', 'movement', 'case_material', 'year', 'condition', 'ref', 'box', 'papers', 'country', 'region',
           'case_diameter', 'price', 'url', 'note', 'hot_48']

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

def get_results(params):
    page, term = params
    # print("thread page:" + str(page))

    url_page = url_template.format(page, page_size, term.replace(" ", "+"))
    result = requests.get(url_page)
    soup = BeautifulSoup(result.content, 'lxml')
    content_list = soup.findAll("div", class_="article-item-container wt-search-result")
    for x in content_list:
        content = []
        url_segment = x.find("a")['href']
        id = x.find("a")['data-article-id']
        # print(id)
        for y in x.text.split("\n"):
            if len(y.strip()) > 0:
                content += [y.strip()]
        # print(content)
        index_list = pd.read_csv(output_file_name_template.format(term), usecols=['id'])
        index_list = index_list.values.tolist()
        if id in index_list:
            break
        item_url = base_url + url_segment
        offset = 0
        note = ""
        if content[0] == "TOP":
            note = "Top"
            offset = 1
        if content[0] == "AUCTION":
            note = "Auction"
            offset = 1
        title = content[0 + offset]
        movement = content[2 + offset]
        case_material = content[4 + offset]
        year = content[6 + offset]
        condition = content[8 + offset]
        ref = content[10 + offset]
        scope = content[12 + offset]
        box, papers = decompose_scope(scope)
        country = content[14 + offset].split(",",1)[0]
        if len(content[14 + offset].split(",",1)) > 1:
            region = content[14 + offset].split(",", 1)[1].strip()
        else:
            region = ""
        case_diameter = content[16 + offset]
        price = content[17 + offset]
        new_entry = pd.DataFrame([[title, movement, case_material, year, condition, ref, box, papers,
                                   country, region, case_diameter, price, item_url, note, ""]], columns=columns, index=[id])
        # print(new_entry)
        csv_output_lock = threading.Lock()
        with csv_output_lock:
            new_entry.to_csv(output_file_name_template.format(term), mode='a', header=False)
    return True

if __name__ == "__main__":
    input_rows = pd.read_csv(term_list_directory, index_col=0)

    for i, row in input_rows.iterrows():
        term = row['term']
        if row['done'] > 0:
            continue

        while True:
            try:
                output = pd.read_csv(output_file_name_template.format(term), index_col=0)
                break
            except FileNotFoundError as e:
                output = pd.DataFrame(columns=columns)
                output.to_csv(term + ".csv", index_label='id')

        url_page = url_template.format(1, page_size, term.replace(" ","+"))
        result = requests.get(url_page)
        soup = BeautifulSoup(result.content,'html.parser')
        links = list(soup.find("div", class_="h1 m-b-0 text-center"))
        num_items = int(links[0].split(" ")[-4].replace(",",""))
        print("Search: " + term)

        num_pages = int(np.ceil(int(num_items)/page_size))
        print("Number of page results: " + str(num_pages))
        page_list = [(i, term) for i in range(num_pages)]

        # for value in page_list:
        #     get_results(value)

        # run threaded scrape
        with ThreadPoolExecutor(max_workers=threads) as executor:
            results = list(tqdm(executor.map(get_results, page_list), total = num_pages))

        if is_deploy_mode:
            term_output = pd.read_csv(output_file_name_template.format(term))
            search_terms.loc[i, 'done'] = len(term_output)
            search_terms.to_csv(term_list_directory)
            print("Completed: " + term)
