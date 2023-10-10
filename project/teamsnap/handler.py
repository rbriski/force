import os
import pickle
import time
from typing import Dict, List

from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait


class Handler:
    LOGIN_URL = "https://go.teamsnap.com/login/signin"

    def __init__(self, username: str, password: str):
        self.options = webdriver.ChromeOptions()
        self.options.add_argument("--incognito")
        self.options.add_argument("--verbose")
        self.username = username
        self.password = password
        self.driver = webdriver.Chrome(options=self.options)

    def login(self) -> None:
        """
        Logs into the website using provided username and password.
        """

        self.driver.get(self.LOGIN_URL)

        # Find and fill the login form
        email_elem = self.driver.find_element(By.NAME, "login")
        password_elem = self.driver.find_element(By.NAME, "password")
        email_elem.send_keys(self.username)
        password_elem.send_keys(self.password)

        # Optionally check the 'keep me logged in' checkbox
        keep_logged_in_elem = self.driver.find_element(By.NAME, "keep_logged_in")
        keep_logged_in_elem.click()

        # Submit the form
        login_button = self.driver.find_element(By.NAME, "submit")
        login_button.click()

        time.sleep(5)

        # Save the cookies for future use
        pickle.dump(self.driver.get_cookies(), open("cookies.pkl", "wb"))

    def get_source(self, url: str, wait_for_xpath: str | None = None) -> str:
        """
        Fetches the page source after loading the stored cookies.
        If cookies.pkl doesn't exist or the session has expired,
        it tries to log in using the provided username and password.

        Args:
        - url (str): URL to fetch.

        Returns:
        - str: HTML source of the loaded page.
        """

        # Check if cookies.pkl exists, if not, attempt to login
        if not os.path.exists("cookies.pkl"):
            self.login()

        self.driver.get(self.LOGIN_URL)

        # Load and set cookies for the session
        cookies: List[Dict[str, str]] = pickle.load(open("cookies.pkl", "rb"))
        for cookie in cookies:
            self.driver.add_cookie(cookie)

        self.driver.get(url)
        if wait_for_xpath:
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.XPATH, wait_for_xpath))
            )

        # Check if we were redirected back to login page
        if self.driver.current_url == self.LOGIN_URL:
            self.login()
            self.driver.get(url)  # Try accessing the URL again after logging in
            if wait_for_xpath:
                WebDriverWait(self.driver, 10).until(
                    EC.presence_of_element_located((By.XPATH, wait_for_xpath))
                )

        # Remove the cookie banner if it exists
        try:
            ok_button = self.driver.find_element(
                By.ID, "CybotCookiebotDialogBodyButtonAccept"
            )
            ok_button.click()
        except NoSuchElementException:
            print("OK button not found on the page.")

        return self.driver.page_source

    def dashboard(self) -> str:
        """
        Fetches the page source of the dashboard.

        Returns:
        - str: HTML source of the dashboard page.
        """
        return self.get_source(self.DASH_URL)
