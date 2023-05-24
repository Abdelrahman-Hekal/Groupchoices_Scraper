from selenium import webdriver
import undetected_chromedriver.v2 as uc
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait as wait
from selenium.webdriver.common.by import By
from webdriver_manager.chrome import ChromeDriverManager
import pandas as pd
from pathlib import Path
import time
import os
import random
import shutil
import time
import unidecode
import calendar

def initialize_bot():

    # Setting up chrome driver for the bot
    chrome_options  = webdriver.ChromeOptions()
    # suppressing output messages from the driver
    chrome_options.add_argument('--log-level=3')
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-gpu')
    chrome_options.add_argument('--disable-extensions')
    chrome_options.add_argument('--window-size=1920,1080')
    # adding user agents
    chrome_options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/87.0.4280.88 Safari/537.36")
    chrome_options.add_argument("--incognito")
    chrome_options.add_experimental_option('excludeSwitches', ['enable-logging'])
    # running the driver with no browser window
    chrome_options.add_argument('--headless')
    # installing the chrome driver
    driver_path = ChromeDriverManager().install()
    # configuring the driver
    driver = webdriver.Chrome(driver_path, options=chrome_options)
    driver.set_page_load_timeout(60)
    driver.maximize_window()

    return driver

def scrape_Groupchoices():

    months = list(calendar.month_name[1:])
    start = time.time()
    print('-'*75)
    print('Scraping Groupchoices.com ...')
    print('-'*75)
    # initialize the web driver
    driver = initialize_bot()

    # initializing the dataframe
    data = pd.DataFrame(columns=['Title', 'Title Link', 'Subtitle', 'Author', 'Genre', 'Subject', 'Guide Year', 'Publisher', 'Release Date', 'Number Of Pages', 'Cover', 'ISBN-13', 'Price', 'Purchase Link'])
    driver.get('https://readinggroupchoices.com/search-books/')
    time.sleep(3)
    n = 0
    while True:
        try:
            # getting the list of books links
            rows = wait(driver, 5).until(EC.presence_of_all_elements_located((By.TAG_NAME, "tr")))[1:]
            nrows = len(rows)
            for i, row in enumerate(rows):
                tds = wait(row, 5).until(EC.presence_of_all_elements_located((By.TAG_NAME, "td")))
                title = tds[0].text.title()
                title = unidecode.unidecode(title)
                title_link = wait(tds[0], 5).until(EC.presence_of_element_located((By.TAG_NAME, "a"))).get_attribute('href')
                author = tds[1].text.title()
                author = unidecode.unidecode(author)
                genre = tds[2].text.title()
                subject = tds[3].text
                guide_year = tds[4].text
                # appending the output to the datafame
                data = data.append([{'Title':title, 'Title Link':title_link, 'Author':author, 'Genre':genre, 'Subject':subject, 'Guide Year':guide_year}])
                print(f'Literature {n+1} link is scraped successfully.')
                n+= 1
            # moving to the next page
            try:
                li = wait(driver, 5).until(EC.presence_of_element_located((By.XPATH, "//li[@class='paginate_button next disabled']")))
                print('-'*75)
                break
            except:
                li = wait(driver, 5).until(EC.presence_of_element_located((By.XPATH, "//li[@id='book-search-table_next']")))
                button = wait(li, 5).until(EC.presence_of_element_located((By.TAG_NAME, "a")))
                driver.execute_script("arguments[0].click();", button)

        except:
            print('Error occurred during the scraping from CliffsNotes.com, retrying ..')
            driver.quit()
            time.sleep(5)
            driver = initialize_bot()

    # scraping books details
    data = data.reset_index(drop = True)
    inds = data.index
    n = len(inds)
    for i in inds:
        
        link = data.loc[i, 'Title Link']
        driver.get(link)
        try:
            subtitle = wait(driver, 5).until(EC.presence_of_element_located((By.CSS_SELECTOR, "h2.book-subtitle"))).get_attribute("textContent")
        except:
            subtitle = ''

        try:
            ul = wait(driver, 5).until(EC.presence_of_element_located((By.CSS_SELECTOR, "ul.list-inline")))
            lis = wait(ul, 5).until(EC.presence_of_all_elements_located((By.TAG_NAME, "li")))
        except:
            pass

        publisher = ''
        release_date = ''
        npages = ''
        ISBN13 = ''
        cover = ''
        order = []
        try:
            for j, li in enumerate(lis):
                text = li.text
                # cover data
                if 'Paperback' in text or 'Hardcover' in text:
                    cover = text
                    order.append(j)
                # number of pages
                elif 'Page' in text:
                    npages = text.split(' ')[0]
                    order.append(j)
                # ISBN
                elif '-' in text or (text.isnumeric() and len(text)>5):
                    ISBN13 = text
                    order.append(j)
                # date
                if release_date == '':
                    words = text.split(' ')
                    # month in the date
                    for word in words:
                        if word in months:
                            release_date = text
                            order.append(j)
                            break
                    # only year in the date
                    if len(text) == 4 and text.isnumeric() and text[:2] == '20' and release_date == '':
                        release_date = text
                        order.append(j)

            # publisher check
            if 0 not in order:
                publisher = lis[0].text
        except:
            #print(f'Warning: Error occurred in getting the details of book: {link}')
            pass

        try:
            div = wait(driver, 5).until(EC.presence_of_element_located((By.CSS_SELECTOR, "div.single-book_purchase-options")))
        except:
            pass

        try:
            price = wait(div, 5).until(EC.presence_of_element_located((By.TAG_NAME, "p"))).text.replace('$', '')
        except:
            price = ''

        try:
            book_link = wait(div, 5).until(EC.presence_of_all_elements_located((By.TAG_NAME, "a")))[0].get_attribute('href')
        except:
            book_link = ''

        data.loc[i, 'Subtitle'] = subtitle
        data.loc[i, 'Publisher'] = publisher
        data.loc[i, 'Release Date'] = release_date
        data.loc[i, 'Number Of Pages'] = npages
        data.loc[i, 'ISBN-13'] = ISBN13
        data.loc[i, 'Price'] = price
        data.loc[i, 'Purchase Link'] = book_link
        data.loc[i, 'Cover'] = cover
        print(f'Literature {i+1}/{n} Details are scraped successfully.')
    # optional output to csv
    data.to_csv('Groupchoices_data.csv', encoding='UTF-8', index=False)
    elapsed = round((time.time() - start)/60, 2)
    print('-'*75)
    print(f'Groupchoices.com scraping process completed successfully! Elapsed time {elapsed} mins')
    print('-'*75)

    driver.quit()
    return data

if __name__ == "__main__":

    data = scrape_Groupchoices()

