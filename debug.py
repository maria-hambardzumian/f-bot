from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service

chrome_options = Options()
chrome_options.add_argument("--headless")
chrome_options.add_argument("--no-sandbox")
chrome_options.add_argument("--disable-dev-shm-usage")
chrome_options.add_argument("--window-size=1920,1180")
chrome_options.add_argument("--disable-gpu") # Try adding this

try:
    service = Service("/usr/bin/chromedriver")
    driver = webdriver.Chrome(service=service, options=chrome_options)
    driver.get("about:blank") # Just try to open a blank page
    print("Chrome launched successfully!")
    driver.quit()
except Exception as e:
    print(f"Failed to launch Chrome: {e}")
