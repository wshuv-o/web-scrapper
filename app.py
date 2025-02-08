from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from time import sleep
from bs4 import BeautifulSoup
import pandas as pd
from random import shuffle
import wget
import os

def GetURL(driver):
    page_source = BeautifulSoup(driver.page_source, 'html.parser')
    results = page_source.find_all('li', class_='reusable-search__result-container')

    all_profiles = []

    for result in results:
        spanprofile = result.find('span', class_='entity-result__title-text')
        profile = spanprofile.find('a', class_='app-aware-link')
        spans = profile.find_all('span')
        prof_ID = profile.get('href')
        subtitle = result.find('div', class_='entity-result__primary-subtitle')
        image = result.find('img', class_='presence-entity__image')
        secsubtitle = result.find('div', class_='entity-result__secondary-subtitle')

        if len(spans) == 0:
            continue

        name = spans[0].find_all('span')[0].text
        firstname = name.split(' ')[0]
        lastname = name.split(' ')[1]
        job = subtitle.text.replace('\n', '') if subtitle else 'Blank'
        loc = secsubtitle.text.replace('\n', '') if secsubtitle else 'Blank'
        img = image.get('src') if image else 'Blank'

        all_profiles.append([firstname, lastname, job, loc, img])

    return all_profiles

def main():
    # Set up headless mode to run in the background (no GUI)
    options = Options()
    options.add_argument('--headless')
    options.add_argument('--disable-gpu')
    options.add_argument('--no-sandbox')
    
    driver = webdriver.Chrome(options=options)

    # Open LinkedIn login page
    url = 'https://www.linkedin.com/login?fromSignIn=true&trk=guest_homepage-basic_nav-header-signin'
    driver.get(url)
    driver.maximize_window()

    # Get login credentials from the text file
    with open('login_credentials.txt', 'r') as credential:
        uname, psd = credential.readlines()

    # Log in to LinkedIn
    email = driver.find_element(By.ID, 'username')
    email.send_keys(uname.strip())
    sleep(2)
    pwd = driver.find_element(By.ID, 'password')
    pwd.send_keys(psd.strip())
    sleep(2)
    signin_button = WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.XPATH, '//*[@id="organic-div"]/form/div[3]/button'))
    )
    signin_button.click()
    sleep(2)

    # Search for a company (e.g., HubSpot)
    search_bar = driver.find_element(By.XPATH, '//*[@id="global-nav-typeahead"]/input')
    search_bar.send_keys('hubspot company')
    sleep(3)
    search_bar.send_keys(Keys.RETURN)
    sleep(2)

    # Navigate to HubSpot's company page
    url2 = 'https://www.linkedin.com/company/hubspot/'
    driver.get(url2)
    sleep(2)

    # Go to the people section under HubSpot
    url3 = 'https://www.linkedin.com/search/results/people/?currentCompany=%5B%2268529%22%5D&origin=COMPANY_PAGE_CANNED_SEARCH&lipi=urn%3Ali%3Apage%3Ad_flagship3_company%3BBNLZg0q1SGWsjcTVnMK5Og%3D%3D'
    driver.get(url3)
    sleep(2)

    # Scrape employee profiles
    number_of_page = 20
    total_profiles = []
    for page in range(1, number_of_page + 1):
        print(f'Scraping page {page}')
        profiles_on_page = GetURL(driver)
        total_profiles.extend(profiles_on_page)

        # Scroll down and click next page
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        sleep(3)
        try:
            next_button = driver.find_element(By.CLASS_NAME, 'artdeco-pagination__button--next')
            next_button.click()
        except:
            print("Next page button not found!")
            break
        sleep(3)

    # Shuffle profiles for randomness
    shuffle(total_profiles)

    # Save data in a DataFrame
    df = pd.DataFrame(total_profiles[:100], columns=['FirstName', 'LastName', 'Job Title', 'Location', 'Image'])

    # Create the Images directory if it doesn't exist
    if not os.path.exists('Images'):
        os.makedirs('Images')

    # Download the images
    for index, row in df.iterrows():
        img_name = f'Images/{row["FirstName"]}{row["LastName"]}.png'
        if row['Image'] != 'Blank':
            wget.download(row['Image'], img_name)

    # Save data to an Excel file
    df.to_excel('Employees_Data.xlsx', index=False)
    print('Data saved to Employees_Data.xlsx')

    # Close the driver after scraping
    driver.quit()

if __name__ == "__main__":
    main()
