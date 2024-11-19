# Import libraries and packages for the project
import json
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

from selenium.webdriver.support.wait import WebDriverWait

print('- Finish importing packages')


# Task 1.1: Open Chrome and Access LinkedIn login site
# options = webdriver.ChromeOptions()
# options = webdriver.ChromeOptions()
# options.add_argument("--headless")
# options.add_experimental_option("detach", True)
# options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/87.0.4280.88 Safari/537.36")

# driver = webdriver.Chrome()
# driver = webdriver.Chrome(options=options)
def scrape_companies(c):
    driver.get(c)
    time.sleep(8)
    srcc = driver.page_source
    soupc = BeautifulSoup(srcc, 'html.parser')
    div_about = soupc.find('div', {'class': 'ember-view'})
    ul_about = div_about.find('ul', {'class': 'org-page-navigation__items'})
    about_href = ul_about[0].find('a', {
        'class': 'ember-view active pv3 ph4 t-16 t-bold t-black--light org-page-navigation__item-anchor'}).get('href')
    about_url = f"https://www.linkedin.com{about_href}"
    urlc = about_url
    driver.get(about_url)
    time.sleep(8)
    about_page = driver.page_source
    about_soup = BeautifulSoup(about_page, 'html.parser')
    name_company = about_soup.find('h1', {
        'class': 'ember-view org-top-card-summary__title text-headling-xlargefull-width inline'}).get_text().strip()
    """if Company.objects.filter(name=name_company).exists():
        print(f"{name_company} already exists in the database. Skipping")
        remainingc_urls = cp_urls[c + 1:]
        random.shuffle(remainingc_urls)

        # Replace the remaining part of the list with the shuffled URLs
        cp_urls = cp_urls[:c + 1] + remainingc_urls
        continue"""
    about_section = about_soup.find('section', {
        'class': 'artdeco-card org-page details-module__card-spacing artdeco-card org-about-module__margin-bottom'})
    details = about_section.find('div', {'class': 'overflow hidden'})
    nbr = len(details)
    # website = about_section.find('a', {'id': 'ember54'}).get('href')
    for i in range(1, nbr + 1):
        key = details.find('h3', {'class': 'text-heading-medium'}).get_text().strip()
        value = details.find('dd', {'class': 'mb4 t-black--light text-body-medium'})
        if key is None or value is None:
            print(f"Error scraping details for {name}: {value}")
        else:
            if key == 'website':
                value = value.find('a', {'class': 'link-without-visited-state ember-view'}).get('href')
            elif key == 'company size' or key == 'Founded':
                continue
            company_details[key] = value.get_text().strip()
    company_details['name'] = name_company
    company_details['url'] = urlc
    return company_details


##############################
# using chromedriver
chrome_driver_path = 'C:/chromedriver-win64/chromedriver.exe'
service = Service(chrome_driver_path)
options = webdriver.ChromeOptions()
# options.add_argument("--window-size=1920x1080")
# options.add_argument("--disable-gpu")
# options.add_argument("--disable-dev-shm-usage")
# options.add_argument("--no-sandbox")

driver = webdriver.Chrome(service=service)
driver.get("https://www.linkedin.com/login/")
try:
    with open('data/linkedin_cookies.json', 'r') as file:
        cookies = json.load(file)
    for cookie in cookies:
        driver.add_cookie(cookie)
    print("Cookies loaded successfully.")
except FileNotFoundError:
    print("No cookies file found. Please run save_cookies.py first.")

"""try:
    driver.get("https://www.linkedin.com/login/")
    # Task 1.2: Import username and password
    credential = open('credentials.txt')
    line = credential.readline()
    credentials = line.split()
    username = credentials[0]
    password = credentials[1]
    print(username, password)
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

    print('- Finish Task 1: Login to Linkedin')"""

driver.refresh()
# driver.get('https://www.linkedin.com')

# Define the base LinkedIn URL and query parameters
base_url = "https://www.linkedin.com/search/results/people/"

# Query parameters
industries = ["Software Development", "Information Technology & Services", "Telecommunications"
              ]  # Example industry codes as strings
job_titles = ["Directeur des Partenariats", "Chef de Produit", "Responsable Marketing", "HR manager"]
keywords = "hr manager"
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
try:
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

        uls = soup.find('ul', {'class': 'reusable-search__entity-result-list list-style-none'})

        if uls is None:
            print("Could not find 'ul' element with class 'display-flex list-style-none flex-wrap'")
        else:
            pr_urls = []
            for li in uls.findAll('li'):
                try:
                    r = li.find('a', {'class': 'app-aware-link scale-down'}).get('href')
                    parsed_urlp = urllib.urlparse(r)
                    base_urlp = f"{parsed_urlp.scheme}://{parsed_urlp.netloc}{parsed_urlp.path}"
                    if Person.objects.filter(url__startswith=base_urlp).exists():
                        print(f"{base_urlp} already exists in the database. Skipping.")
                        continue

                    pr_urls.append(r)
                except Exception as e:
                    print(f"Error processing 'li' element: {e}")

            random.shuffle(pr_urls)  # Randomize the order of profiles before scraping
            print(f"len(out): {len(pr_urls)}")
            contacts = []
            companies = []

            cp_urls = []
            new_contacts_count = 0
            new_companies_count = 0
            for s, p in enumerate(pr_urls):
                try:
                    driver.get(p)
                    time.sleep(8)
                    src = driver.page_source
                    soup = BeautifulSoup(src, 'html.parser')
                    urlp = p
                    name = soup.find('h1', {
                        'class': 'text-heading-xlarge inline t-24 v-align-middle break-words'}).get_text().strip()
                    if Person.objects.filter(name=name).exists():
                        print(f"{name} already exists in the database. Skipping. len(out): {len(pr)}")
                        remaining_urls = pr[s + 1:]
                        random.shuffle(remaining_urls)

                        # Replace the remaining part of the list with the shuffled URLs
                        pr = pr[:s + 1] + remaining_urls

                        continue
                    # title = soup.find('div', {'class': 'text-body-medium break-words'}).get_text().strip()
                    location = soup.find('span', {
                        'class': 'text-body-small inline t-black--light break-words'}).get_text().strip()
                    # dets = soup.find_all('div', {'class': 'inline-show-more-text--is-collapsed'})
                    # company_name = dets[0].get_text().strip() if dets else ''

                    Esection_tag = soup.find('section', {
                        'class': 'artdeco-card pv-profile-card break-words mt2'})
                    Euls = Esection_tag.findAll('ul')
                    company_url = Euls[0].find('a', {'class': 'optional-action-target-wrapper display-flex'}).get(
                        'href')
                    title = Euls[0].find('div',
                                         {'class': 'display-flex align-items-center mr1 t-bold'}).get_text().strip()
                    company_name = Euls[0].find('span', {'class': 't-14 t-normal'}).get_text().strip()
                    if company_url.contains("/results"):
                        print("error handeling data")
                        continue
                    else:
                        parsed_url = urllib.urlparse(company_url)
                        base_urlc = f"{parsed_url.scheme}://{parsed_url.netloc}{parsed_url.path}"
                        if Company.objects.filter(url__startswith=base_urlc).exists():
                            print(f"{base_urlc} already exists in the database. Skipping.")
                        else:
                            #cp_urls.append(company_url)

                            company_details = dict()
                            try:
                                company_details = scrape_companies(c)

                            except Exception as e:
                                print(f"An error occurred during company scraping process: {e}")

                            companies.append(company_details)
                            print(f"Scraped data for {company_name}: {company_details}")
                    person = {"url": urlp, "name": name, "title": title, "location": location,
                              "company": company_name}

                    contacts.append(person)
                    print(f"Scraped data for {name}: {person}")

                    for company_data in companies:
                        company, created = Company.objects.update_or_create(
                            name=company_data["name"],
                            defaults={
                                "industry": company_data["Industry"],
                                "phone": company_data["Phone"],
                                "location": company_data["Headquarters"],
                                "website_url": company_data["Website"],
                                "url": company_data["url"],
                            }
                        )
                        print(f"Company {'created' if created else 'updated'}: {company.name}")

                    Person.objects.update_or_create(
                        name=name,
                        company=company,
                        defaults={
                            'url': url,
                            'email': email,
                            'title': title,
                            'location': location,
                            'img_url': img_url
                        }
                    )

                    progress_step = len(contacts)
                    progress_percent = (progress_step / ct_num) * 100

                    new_contacts_count += 1
                    redis_conn.set('scraped_data', json.dumps(out))
                    redis_conn.set('scraping_progress', json.dumps(
                        {'progress': progress_percent, 'step': progress_step, 'total_steps': st_num}))

                    if new_people_count >= ct_num:
                        break  # Stop when we've added the required number of new people
                    print(progress_percent)
                except Exception as e:
                    print(f"Error scraping profile {p}: {e}")
                print(pr_urls)
                print(contacts)
                print(cp_urls)
            redis_conn.set('scraped_data', json.dumps(out))
except Exception as e:
    print(f"An error occurred during the scraping process: {e}")
    redis_conn.set('scraped_data', json.dumps([]))


finally:
    driver.quit()

# url = 'https://www.linkedin.com/search/results/people/?keywords=hr%20manager&origin=SWITCH_SEARCH_VERTICAL&sid=Wg!'
# url1 = 'https://www.linkedin.com/search/results/people/?industry=%5B%226%22%2C%224%22%5D&keywords=hr%20manager&origin=FACETED_SEARCH&sid=g4*'

# Task 2: Search for the profile we want to crawl
# Wait for the search field to load, then access it
# search_field = WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.XPATH, '//input[@aria-label="Search"]')))

""" # Apply industry filter (optional)
    if industry_filter:
        industry_button = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.XPATH, '//button[contains(text(), "Industry")]'))
        )
        industry_button.click()
        industry_input = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.XPATH, '//input[contains(@placeholder, "Add an industry")]'))
        )
        industry_input.send_keys(industry_filter)
        industry_input.send_keys(Keys.RETURN)
        time.sleep(3)  # Wait for the filter to apply

    print("Search with filters applied successfully!")

except Exception as e:
    print(f"An error occurred: {e}")

finally:
    # Close the driver if needed
    driver.quit()"""

"""search_field = driver.find_element(By.XPATH, "//input[@aria-label='Search']")
print('- Finish Task 2: Search for profilesf')
# Enter a search query (e.g., 'Tech Companies')
search_field.send_keys("HR Manager")

# Press Enter to initiate the search
search_field.send_keys(Keys.RETURN)

print("Search executed successfully!")

# Task 2.1: Locate the search bar element
#search_field = driver.find_element(By.CLASS_NAME, "input.search-global-typeahead__input")

# Task 2.2: Input the search query to the search bar
#search_query = input('What Tech Companies do you want to scrape? ')
#search_field.send_keys(search_query)

# Task 2.3: Search
#search_field.send_keys(Keys.RETURN)

print('- Finish Task 2: Search for profiles')"""

# Task 3: Scrape the URLs of the profiles

# Task 3.1: Write a function to extract the URLs of one page
"""def GetURL():
    page_source = BeautifulSoup(driver.page_source, "html.parser")
    profiles = page_source.find_all('a', class_='app-aware-link ')
    all_profile_URL = []
    for profile in profiles:
        profile_ID = profile.get('href')

        profile_URL = "https://www.linkedin.com/in/" + profile_ID
        if profile_URL not in all_profile_URL:
            all_profile_URL.append(profile_URL)
    return all_profile_URL"""

# links = soup.find_all('a')
# urls = [link.get('href') for link in links]
# print(urls)


# Task 3.2: Navigate through many page, and extract the profile URLs of each page

"""input_page = int(input('How many pages you want to scrape: '))
URLs_all_page = []
for page in range(input_page):
    URLs_one_page = GetURL()
    sleep(2)
    driver.execute_script('window.scrollTo(0, document.body.scrollHeight);')  #scroll to the end of the page
    sleep(3)
    next_button = driver.find_element(By.XPATH, "//button[@aria-label='Next']")
    driver.execute_script("arguments[0].click();", next_button)
    URLs_all_page.append(URLs_one_page)
    sleep(2)

print('- Finish Task 3: Scrape the URLs')"""

# Task 4: Scrape the data of 1 Linkedin profile, and write the data to a .CSV file

# """with open('output.csv', 'w',  newline = '') as file_output:
""" headers = ['Name', 'Job Title', 'Location', 'LinkedInURL', 'Company', 'CompanyURL']
    writer = csv.DictWriter(file_output, delimiter=',', lineterminator='\n',fieldnames=headers)
    writer.writeheader()
    for linkedin_URL in URLs_all_page:
        driver.get(linkedin_URL)
        print('- Accessing profile: ', linkedin_URL)

        page_source = BeautifulSoup(driver.page_source, "html.parser")

        info_div = page_source.find('div',{'class':'flex-1 mr5'})
        info_loc = info_div.find_all('ul')
        name = info_loc[0].find('li').get_text().strip() #Remove unnecessary characters
        print('--- Profile name is: ', name)
        location = info_loc[1].find('li').get_text().strip() #Remove unnecessary characters
        print('--- Profile location is: ', location)
        title = info_div.find('h2').get_text().strip()
        print('--- Profile title is: ', title)
        writer.writerow({headers[0]:name, headers[1]:location, headers[2]:title, headers[3]:linkedin_URL})
        print('\n')

print('Mission Completed!')"""
