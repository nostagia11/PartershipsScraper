
import json

from redis import Redis

from Pscraper.models import Person
from Pscraper.models import Company
import random
import re
import time
from time import sleep

from selenium.webdriver.support import expected_conditions as EC

from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from bs4 import BeautifulSoup

import urllib
from urllib.parse import urlparse
from celery import shared_task
from selenium.webdriver.support.wait import WebDriverWait


@shared_task
def scrape_linkedin (ct_num, title):
    # Task 1.1: Open Chrome and Access LinkedIn login site
    # options = webdriver.ChromeOptions()
    # options = webdriver.ChromeOptions()
    # options.add_argument("--headless")
    # options.add_experimental_option("detach", True)
    # options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/87.0.4280.88 Safari/537.36")

    # driver = webdriver.Chrome()
    # driver = webdriver.Chrome(options=options)
    redis_conn = Redis(host='192.168.0.18', port=6379, db=1)
    ##############################
    # using chromedriver
    chrome_driver_path = 'C:/chromedriver-win64/chromedriver.exe'
    service = Service(chrome_driver_path)
    options = webdriver.ChromeOptions()
    options.add_argument("--window-size=1920x1080")
    # options.add_argument("--disable-gpu")
    # options.add_argument("--disable-dev-shm-usage")
    """options.add_argument("--no-sandbox")"""

    driver = webdriver.Chrome(service=service, options=options)

    try:
        driver.get("https://www.linkedin.com/login/")
        # Task 1.2: Import username and password
        credential = open('credentials.txt')
        line = credential.readlines()
        username = line[0].strip()
        password = line[1].strip()
        print('- Finish importing the login credentials')
        sleep(2)

        # Task 1.2: Key in login credentials
        email_field = driver.find_element(By.ID, 'username')
        email_field.send_keys(username)
        print('- Finish keying in email')
        sleep(3)

        password_field = driver.find_element(By.ID, 'password')
        password_field.send_keys(password)
        print('- Finish keying in password')
        sleep(2)

        # Task 1.2: Click the Login button
        signin_field = driver.find_element(By.XPATH, '//button[@type="submit"]')
        signin_field.click()

        # password_field.submit()
        # Locate and click the 'Sign in' button
        # sign_in_button = (WebDriverWait(driver, 10)
        # .until(EC.element_to_be_clickable((By.XPATH, '//button[@type="submit"]'))))
        # sign_in_button.click()
        sleep(3)

        print('- Finish Task 1: Login to Linkedin')

        options.add_argument("--headless")
        driver = webdriver.Chrome(service=service, options=options)
        driver.get('https://www.linkedin.com')

        # Define the base LinkedIn URL and query parameters
        base_url = "https://www.linkedin.com/search/results/people/"

        # Query parameters
        industries = ["Software Development", "Information Technology & Services", "Telecommunications"
                      ]  # Example industry codes as strings
        job_titles = ["Directeur des Partenariats", "Chef de Produit", "Responsable Marketing", "HR manager"]
        keywords = title
        origin = "FACETED_SEARCH"
        sid = "ltS"

        # Encode the list of industries as a JSON array and URL encode the entire query string
        query_params = {
            "industry": urllib.parse.quote(f'[{",".join([f"{industry}" for industry in industries])}]'),
            "keywords": keywords,
            "origin": origin,
            "sid": sid
        }

        # Combine base URL with the encoded query parameters
        url = f"{base_url}?{urllib.parse.urlencode(query_params)}"
        driver.get(url)

        total_scrolls = 5
        last_height = driver.execute_script("return document.body.scrollHeight")

        for i in range(total_scrolls):
            scroll_height = driver.execute_script("return document.body.scrollHeight")
            driver.execute_script(f'window.scrollTo(0, {scroll_height});')

            # Random delay between scrolls
            time.sleep(random.uniform(3, 6))

            new_height = driver.execute_script("return document.body.scrollHeight")
            if new_height == last_height:
                break
            last_height = new_height

        src = driver.page_source
        soup = BeautifulSoup(src, 'html.parser')
        print(soup)
        uls = soup.find('ul', {'class': 'display-flex list-style-none flex-wrap'})

        if uls is None:
            print("Could not find 'ul' element with class 'display-flex list-style-none flex-wrap'")
            redis_conn.set('scraped_data', json.dumps([]))
        else:
            pr = []
            for li in uls.findAll('li'):
                try:
                    r = li.find('a', {'class': 'app-aware-link'}).get('href')
                    parsed_url = urllib.urlparse(r)
                    base_urlp = f"{parsed_url.scheme}://{parsed_url.netloc}{parsed_url.path}"
                    if Person.objects.filter(url__startswith=base_urlp).exists():
                        print(f"{base_url} already exists in the database. Skipping.")
                        continue
                    pr.append(r)
                except Exception as e:
                    print(f"Error processing 'li' element: {e}")

            random.shuffle(pr)  # Randomize the order of profiles before scraping
            print(f"len(out): {len(pr)}")
            out = []
            companies = []
            new_contacts_count = 0
            new_companies_count = 0
            for c, p in enumerate(pr):
                try:
                    driver.get(p)
                    time.sleep(8)
                    src = driver.page_source
                    soup = BeautifulSoup(src, 'html.parser')
                    url = p
                    name = soup.find('h1', {
                        'class': 'text-heading-xlarge inline t-24 v-align-middle break-words'}).get_text().strip()
                    if Person.objects.filter(name=name).exists():
                        print(f"{name} already exists in the database. Skipping. len(out): {len(pr)}")
                        remaining_urls = pr[c + 1:]
                        random.shuffle(remaining_urls)

                        # Replace the remaining part of the list with the shuffled URLs
                        pr = pr[:c + 1] + remaining_urls

                        continue
                    # title = soup.find('div', {'class': 'text-body-medium break-words'}).get_text().strip()
                    location = soup.find('span', {
                        'class': 'text-body-small inline t-black--light break-words'}).get_text().strip()
                    # dets = soup.find_all('div', {'class': 'inline-show-more-text--is-collapsed'})
                    # company_name = dets[0].get_text().strip() if dets else ''
                    img_tag = soup.find('img', {
                        'class': 'presence-entity__image ivm-view-attr__img--centered EntityPhoto-circle-3 EntityPhoto-circle-3  evi-image lazy-image ember-view'})
                    img_url = img_tag['src'] if img_tag else ''

                    Esection_tag = soup.find('section', {
                        'class': 'artdeco-card pv-profile-card break-words mt2'})
                    Euls = Esection_tag.findAll('ul')
                    company = Euls[0].find('a', {'class': 'optional-action-target-wrapper display-flex'}).get('href')
                    parsed_urlc = urllib.urlparse(r)
                    base_urlc = f"{parsed_urlc.scheme}://{parsed_urlc.netloc}{parsed_urlc.path}"
                    if Company.objects.filter(url__startswith=base_urlc).exists():
                        print(f"{base_url} already exists in the database. Skipping.")
                        continue
                    companies.append(company)
                    title = Euls[0].find('div',
                                         {'class': 'display-flex align-items-center mr1 t-bold'}).get_text().strip()
                    company_name = Euls[0].find('span', {'class': 't-14 t-normal'}).get_text().strip()
                    person = {"url": url, "name": name, "title": title, "location": location,
                              "company": company_name, "img_url": img_url}

                    out.append(person)
                    print(f"Scraped data for {name}: {person}")
                    progress_step = len(out)
                    progress_percent = (progress_step / ct_num) * 100
                    redis_conn.set('scraped_data', json.dumps(out))
                    redis_conn.set('scraping_progress', json.dumps(
                        {'progress': progress_percent, 'step': progress_step, 'total_steps': ct_num}))
                    new_contacts_count += 1
                    new_companies_count += 1


                    if new_contacts_count >= ct_num:
                        break  # Stop when we've added the required number of new people
                    print(progress_percent)
                except Exception as e:
                    print(f"Error scraping profile {p}: {e}")
            redis_conn.set('scraped_data', json.dumps(out))
            print(pr)
            print(out)
            print(companies)
    except Exception as e:
        print(f"An error occurred during the scraping process: {e}")


    finally:
        driver.quit()
