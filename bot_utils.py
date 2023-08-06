from selenium import webdriver
from selenium.webdriver.chrome.options import Options as ChromeOptions
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.by import By
from selenium.webdriver.edge.options import Options as EdgeOptions
from selenium.webdriver.firefox.options import Options as FirefoxOptions
from selenium.webdriver.safari.options import Options as SafariOptions


class Utils:
    debug = False

    def __init__(self, debug):
        self.debug = debug

    def setup_driver(self, browser, headless):
        chrome_options = ChromeOptions()
        firefox_options = FirefoxOptions()
        edge_options = EdgeOptions()
        safari_options = SafariOptions()
        if headless:
            if browser == "opera" or browser == "phantomjs":
                print("Browser not supported in headless mode")
                exit(1)
            chrome_options.add_argument("--headless")
            firefox_options.add_argument("--headless")
            edge_options.add_argument("--headless")
            safari_options.add_argument("--headless")

        if browser == "chrome":
            drv = webdriver.Chrome(options=chrome_options)
        elif browser == "firefox":
            drv = webdriver.Firefox(options=firefox_options)
        elif browser == "edge":
            drv = webdriver.Edge(options=edge_options)
        elif browser == "safari":
            drv = webdriver.Safari(options=safari_options)
        else:
            print("Browser not supported")
            exit(1)
        self.drv = drv
        return drv

    def setup_action_chains(self, drv):
        self.act = ActionChains(drv)
        return ActionChains(drv)

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

    def get_image(self, xpath):
        if self.debug:
            print("Getting image from " + xpath)
        while True:
            try:
                return self.drv.find_element(By.XPATH, xpath).get_attribute("src")
            except:
                continue

    def open_link_in_new_tab(self, xpath):
        if self.debug:
            print("Opening link in new tab " + xpath)
        while True:
            try:
                link = (self.drv.find_element(
                    By.XPATH, xpath).get_attribute("href"))
            except:
                continue
            break
        self.drv.execute_script("window.open("");")
        self.drv.switch_to.window(self.drv.window_handles[1])
        self.drv.get(link)

    def send_keys(self, keys):
        self.act.send_keys(keys).perform()
