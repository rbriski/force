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
# Navigate to the website
url = "https://go.teamsnap.com/login/"  # Replace this with the actual URL
driver.get(url)

# Find the email and password fields using their name attributes
email_elem = driver.find_element(By.NAME, "login")
password_elem = driver.find_element(By.NAME, "password")

# Fill out the fields
email_elem.send_keys("rbriski@gmail.com")
password_elem.send_keys("2cd9Zs6pWLur&i2t[QjWB)Vg")

# Optionally, if you want to keep logged in, check the checkbox
keep_logged_in_elem = driver.find_element(By.NAME, "keep_logged_in")
keep_logged_in_elem.click()

# Click the login button to submit
login_button = driver.find_element(By.NAME, "submit")
login_button.click()


time.sleep(5)
pickle.dump(driver.get_cookies(), open("cookies.pkl", "wb"))
# wait = WebDriverWait(driver, 10)
# wait.until(EC.text_to_be_present_in_element((By.TAG_NAME, "b"), "Force 10G ECNL"))

driver.quit()
