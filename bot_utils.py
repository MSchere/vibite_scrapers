import urllib.request
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.firefox.service import Service as FirefoxService
from selenium import webdriver
from selenium.webdriver.chrome.options import Options as ChromeOptions
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.by import By
from selenium.webdriver.edge.options import Options as EdgeOptions
from selenium.webdriver.firefox.options import Options as FirefoxOptions
from selenium.webdriver.safari.options import Options as SafariOptions


class Utils:
    debug = False

    def __init__(self, browser, server, headless, debug):
        self.browser = browser
        self.server = server
        self.headless = headless
        self.debug = debug

    def setup_driver(self):
        chrome_options = ChromeOptions()
        firefox_options = FirefoxOptions()
        edge_options = EdgeOptions()
        safari_options = SafariOptions()
        if self.headless:
            if self.browser == "opera" or self.browser == "phantomjs":
                print("Browser not supported in headless mode")
                exit(1)
            chrome_options.add_argument("--window-size=1920,1080")
            chrome_options.add_argument("--headless")
            firefox_options.add_argument("--width=1920")
            firefox_options.add_argument("--height=1080")
            firefox_options.add_argument("--headless")
            edge_options.add_argument("--headless")
            safari_options.add_argument("--headless")

        if self.browser == "chrome":
            if self.server:
                service = ChromeService(
                    "/usr/lib/chromium-browser/chromedriver")
                drv = webdriver.Chrome(service=service, options=chrome_options)
            else:
                drv = webdriver.Chrome(options=chrome_options)
        elif self.browser == "firefox":
            if self.server:
                service = FirefoxService("/usr/local/bin/geckodriver")
                drv = webdriver.Firefox(
                    service=service, options=firefox_options)
            else:
                drv = webdriver.Firefox(options=firefox_options)
        elif self.browser == "edge":
            drv = webdriver.Edge(options=edge_options)
        elif self.browser == "safari":
            drv = webdriver.Safari(options=safari_options)
        else:
            print("Browser not supported")
            exit(1)
        self.drv = drv
        return drv

    def setup_action_chains(self, drv):
        self.act = ActionChains(drv)
        return ActionChains(drv)

    def is_element_present(self, xpath):
        if self.debug:
            print("Checking if element is present " + xpath)
        try:
            self.drv.find_element(By.XPATH, xpath)
        except:
            return False
        return True

    def is_class_present(self, class_name):
        if self.debug:
            print("Checking if class is present " + class_name)
        try:
            self.drv.find_element(By.CLASS_NAME, class_name)
        except:
            return False
        return True

    def find(self, xpath):
        if self.debug:
            print("Finding " + xpath)
        try:
            return self.drv.find_element(By.XPATH, xpath).text
        except:
            raise Exception("Unable to locate element")

    def click(self, xpath):
        if self.debug:
            print("Clicking " + xpath)
        while True:
            try:
                self.drv.find_element(By.XPATH, xpath).click()
            except:
                continue
            break

    def input_text(self, text, xpath):
        if self.debug:
            print("Inputting text " + text + " in " + xpath)
        while True:
            try:
                self.drv.find_element(By.XPATH, xpath).send_keys(text)
            except:
                continue
            break

    def input_text_by_css(self, text, css):
        if self.debug:
            print("Inputting text " + text + " in " + css)
        while True:
            try:
                self.drv.find_element(By.CSS_SELECTOR, css).send_keys(text)
            except:
                continue
            break

    def get_text(self, xpath):
        if self.debug:
            print("Getting text from " + xpath)
        while True:
            try:
                return self.drv.find_element(By.XPATH, xpath).text
            except:
                continue

    def get_text_from_xpaths(self, xpath_list):
        if self.debug:
            print("Getting text from one of " + str(xpath_list))
        for xpath in xpath_list:
            try:
                text = self.drv.find_element(By.XPATH, xpath).text
                if text != "":
                    return text
            except:
                continue

    def get_image(self, xpath):
        if self.debug:
            print("Getting image from " + xpath)
        while True:
            try:
                return self.drv.find_element(By.XPATH, xpath).get_attribute("src")
            except:
                continue

    def download_image(self, xpath):
        if self.debug:
            print("Downloading image from " + xpath)
        while True:
            path = "downloads/images/"
            try:
                image = self.drv.find_element(
                    By.XPATH, xpath).get_attribute("src")
                if image != "":
                    urllib.request.urlretrieve(image, path)
            except:
                continue
            break

    def get_image_from_xpaths(self, xpath_list):
        if self.debug:
            print("Getting image from one of " + str(xpath_list))
        for xpath in xpath_list:
            try:
                image = self.drv.find_element(
                    By.XPATH, xpath).get_attribute("src")
                if image != "":
                    return image
            except:
                continue

    def open_link_in_new_tab(self, xpath):
        while True:
            try:
                link = (self.drv.find_element(
                    By.XPATH, xpath).get_attribute("href"))
                if self.debug:
                    print("Opening link in new tab " + link)
            except:
                continue
            break
        self.drv.execute_script("window.open("");")
        self.drv.switch_to.window(self.drv.window_handles[1])
        self.drv.get(link)

    def send_keys(self, keys):
        self.act.send_keys(keys).perform()
