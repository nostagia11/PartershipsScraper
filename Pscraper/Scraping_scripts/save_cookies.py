import json
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from colorama import Fore, Style, init

# Initialize colorama
init(autoreset=True)

# Path to ChromeDriver
chrome_driver_path = r'C:/chromedriver-win64/chromedriver.exe'  # Update if necessary

# Setting up the Chrome WebDriver
service = Service(chrome_driver_path)
driver = webdriver.Chrome(service=service)

# Open LinkedIn login page
linkedin_url = "https://www.linkedin.com/login"
driver.get(linkedin_url)

# Console messages with color
print(Fore.GREEN + "Opened LinkedIn login page successfully.")
print(Fore.BLUE + "Browser is now waiting for your interaction.")
print(Fore.YELLOW + "Log in manually, and press Enter when done!")

# Wait for manual login
input(Fore.CYAN + "Press Enter after logging in...")

# Save cookies to a file
cookies = driver.get_cookies()
with open('data/linkedin_cookies.json', 'w') as file:
    json.dump(cookies, file)
print(Fore.GREEN + "Session cookies saved successfully.")

# Close the browser
driver.quit()
print(Fore.RED + "Browser closed. Exiting script.")
