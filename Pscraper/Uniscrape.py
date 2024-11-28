# using chromedriver
import re

# Import libraries and packages for the project
import json
import random
import re
import time
from time import sleep

from redis import Redis
from selenium.webdriver.support import expected_conditions as EC

from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from bs4 import BeautifulSoup

import urllib
from urllib.parse import urlparse

from selenium.webdriver.support.wait import WebDriverWait

from Pscraper.models import Person, Company

from bs4 import BeautifulSoup
from selenium.webdriver.chrome import webdriver
from selenium.webdriver.chrome.service import Service

from Pscraper.models import Company


def rot13(s):
    return s.translate(str.maketrans(
        "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz",
        "NOPQRSTUVWXYZABCDEFGHIJKLMnopqrstuvwxyzabcdefghijklm"))


def scrape_uni():
    chrome_driver_path = 'C:/chromedriver-win64/chromedriver.exe'
    service = Service(chrome_driver_path)

    driver = webdriver.Chrome(service=service)
    driver.get(f"https://diplomeo.com/etablissements-ecoles_d_ingenieurs_informatique#ecoles")

    src = driver.page_source
    soup = BeautifulSoup(src, 'html.parser')
    container = soup.find('div', class_='top-video-school')
    ul = container.find('ul', {'data-controller': 'collapse analytics-ecommerce'})

    if ul is None:
        print("Could not find 'ul' element with class 'collapse analytics-ecommerce'")
        # redis_conn.set('scraped_data', json.dumps([]))
    else:
        uni = []
        for li in ul.findAll('li'):
            try:
                uni_div = li.find('div', {'class': 'text'})
                Name_uni = uni_div.find('div', {'class': 'name'}).get_text().strip()
                uni_profile = li.find('div', {'class': 'box'})
                link = uni_profile['data-l']
                location = li.find('div', {'class': 'tag-card'}).get_text()
                img_tag = uni_div.find('img', {'class': 'school-logo'})
                img_url = img_tag['src'] if img_tag else ''
                decoded_link = rot13(link)
                if Company.objects.filter(name=Name_uni).exists():
                    print(f"{Name_uni} already exists in the database. Skipping.")
                continue

                """ base_url = 'https://diplomeo.com/etablissements'
             # Original string with Unicode escape sequences
             original_string = Name_uni

             # Decode the Unicode escape sequences
             decoded_string = original_string.encode().decode('unicode_escape')

             # Replace all non-alphanumeric characters except hyphens with hyphens
             formatted_string = re.sub(r'[^a-zA-Z0-9-]+', '_', decoded_string)

             # Remove extra hyphens (e.g., multiple consecutive hyphens)
             cleaned_string = re.sub(r'_+', '_', formatted_string).strip('_')

             # Combine with the base URL
             final_url = f"{base_url}-{cleaned_string}"

             # Output the result
             print("Formatted URL:", final_url) """

                uni.append(decoded_link)
            except Exception as e:
                print(f"Error processing 'li' element: {e}")

    random.shuffle(uni)  # Randomize the order of profiles before scraping
    print(f"len(uni): {len(uni)}")
    out = []
    uni_count = 0
    for u in enumerate(out):
        try:
            driver.get(u)
            time.sleep(8)
            src = driver.page_source
            # Parse the HTML with BeautifulSoup
            soup = BeautifulSoup(src, 'html.parser')
            links_div = soup.find('div', {'class': 'externals'})
            ul_details = links_div.find('ul')
            if ul_details is None:
                print("Could not find 'ul_details' element '")
            else:
                tag = ul_details[0].find('div', {'class': 'externals_item'})
                encoded_website = tag['data-l']
                website_url = rot13(encoded_website)

                social = soup.find('div', {'class': 'social'})
                social_ul = social.find('ul')
                if social_ul is None:
                    print("Could not find 'social_ul' element '")
                else:
                    l_tag = social_ul[1].find('span')
                    en_url = l_tag ['data-l']
                    linkdihn_url = rot13(en_url)

            company = {"website_url": website_url, "name": Name_uni, "location": location,
                       "img_url": img_url, "url": linkdihn_url}

            out.append(company)
            print(f"Scraped data for {name}: {company}")

            for company_data in out:
                company, created = Company.objects.update_or_create(
                    name=company_data["name"],
                    defaults={
                        "industry": company_data["Industry"],
                        "phone": company_data["Phone"],
                        "location": company_data["location"],
                        "website_url": company_data["Website"],
                        "url": company_data["url"],
                    }
                )
                print(f"Company {'created' if created else 'updated'}: {company.name}")
            progress_step = len(out)
            progress_percent = (progress_step / st_num) * 100
            redis_conn.set('scraped_data', json.dumps(out))
            redis_conn.set('scraping_progress', json.dumps(
                {'progress': progress_percent, 'step': progress_step, 'total_steps': st_num}))
            uni_count += 1
        except Exception as e:
          print(f"Error scraping uni {u}: {e}")
        finally:
            driver.quit()


#redis_conn.set('scraped_data', json.dumps(out))

#except Exception as e:
#print(f"An error occurred during the scraping process: {e}")
#redis_conn.set('scraped_data', json.dumps([]))



# Decode the link if it's encoded (e.g., ROT13 as seen in the attribute)
