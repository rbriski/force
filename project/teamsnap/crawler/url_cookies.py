from selenium import webdriver
from selenium.webdriver.common.by import By
import time
import pickle


# Setup the driver
options = webdriver.ChromeOptions()
# options.add_argument("--headless")
options.add_argument("--incognito")
options.add_argument("--verbose")
driver = webdriver.Chrome(options=options)

url = "https://go.teamsnap.com/login/"  # Replace this with the actual URL
driver.get(url)

cookies = pickle.load(open("cookies.pkl", "rb"))
for cookie in cookies:
    driver.add_cookie(cookie)

# Navigate to the website
url = "https://go.teamsnap.com/team/dashboard"  # Replace this with the actual URL
driver.get(url)

html_after_click = driver.page_source
print(html_after_click)

# ... your further actions ...

# Don't forget to close the driver when done
driver.quit()
