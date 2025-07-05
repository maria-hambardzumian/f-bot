import io
import os
import asyncio
import datetime
from types import SimpleNamespace

from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains
from selenium.common.exceptions import TimeoutException, NoSuchElementException

from telegram import Bot, User, Chat, Message, InputFile

# Environment variables
TOKEN = os.getenv("TELEGRAM_TOKEN")
NUMBER1 = os.getenv("NUMBER1")
NUMBER2 = os.getenv("NUMBER2")
CHAT_ID = os.getenv("CHAT_ID")  # Optional: or hardcode your Telegram ID here

bot = Bot(token=TOKEN)


async def check():
    await bot.send_message(chat_id=CHAT_ID, text="Opening Chrome...")

    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--disable-software-rasterizer")
    chrome_options.add_argument("--window-size=1920,1180")

    service = Service("/usr/bin/chromedriver")  # Works with apt-installed chromedriver
    driver = webdriver.Chrome(service=service, options=chrome_options)

    try:
        driver.get("https://roadpolice.am/hy")

        # --- (Your existing selenium logic unchanged below) ---
        button_span = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR,
                "#index_page_steps > div > div > div > div:nth-child(3) > button > span > span"))
        )
        button = button_span.find_element(By.XPATH, "./ancestor::button")
        button.click()

        await asyncio.sleep(0.2)

        actions = ActionChains(driver)
        actions.send_keys(Keys.TAB).pause(0.4).send_keys(Keys.TAB).perform()
        await asyncio.sleep(1)

        active_element = driver.switch_to.active_element
        for digit in NUMBER1:
            active_element.send_keys(digit)
            await asyncio.sleep(0.1)

        actions.send_keys(Keys.TAB).perform()
        await asyncio.sleep(0.3)

        active_element = driver.switch_to.active_element
        for digit in NUMBER2:
            active_element.send_keys(digit)
            await asyncio.sleep(0.1)

        actions.send_keys(Keys.TAB).perform()
        await asyncio.sleep(0.5)

        submit_button = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, "#hqb-login-submit"))
        )
        submit_button.click()
        await asyncio.sleep(1.5)

        dropdown = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR,
                "body > div > main > div.info-section.info-section--without-cover.pr > div > div > div.info-section__group-item.pr.license-hqb-register > form > div:nth-child(2) > span > span.selection > span"))
        )
        dropdown.click()
        await asyncio.sleep(0.3)
        actions.send_keys(Keys.ARROW_DOWN).pause(0.1).send_keys(Keys.ARROW_DOWN).pause(0.1).send_keys(Keys.ENTER).perform()
        await asyncio.sleep(0.5)

        second_dropdown = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR,
                "body > div > main > div.info-section.info-section--without-cover.pr > div > div > div.info-section__group-item.pr.license-hqb-register > form > div:nth-child(3) > span > span.selection > span"))
        )
        second_dropdown.click()
        await asyncio.sleep(0.3)
        actions.send_keys(Keys.ARROW_DOWN).pause(0.1).send_keys(Keys.ARROW_DOWN).pause(0.1).send_keys(Keys.ENTER).perform()
        await asyncio.sleep(1.5)

        calendar_label = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR,
                "body > div.wrapper > main > div.info-section.info-section--without-cover.pr > div > div > div.info-section__group-item.pr.license-hqb-register > form > div:nth-child(4) > label"))
        )
        calendar_label.click()
        await asyncio.sleep(0.5)

        while True:
            try:
                day_container = WebDriverWait(driver, 5).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR,
                        "div.flatpickr-calendar.open .flatpickr-days .dayContainer"))
                )
                days = day_container.find_elements(By.CSS_SELECTOR, "span")

                found_next_month_day = False

                for day in days:
                    classes = day.get_attribute("class") or ""

                    if "flatpickr-disabled" in classes or "prevMonthDay" in classes:
                        continue
                    elif "nextMonthDay" in classes:
                        found_next_month_day = True
                        break
                    else:
                        aria_label = day.get_attribute("aria-label")
                        day.click()
                        await asyncio.sleep(4)
                        screenshot = driver.get_screenshot_as_png()
                        bio = io.BytesIO(screenshot)
                        bio.name = "valid_date.png"
                        bio.seek(0)

                        await bot.send_photo(
                            chat_id=CHAT_ID,
                            photo=InputFile(bio),
                            caption=f"Առաջին հասանելի օրն է՝ {aria_label}"
                        )
                        return

                if found_next_month_day:
                    next_month_button = WebDriverWait(driver, 3).until(
                        EC.element_to_be_clickable((By.CSS_SELECTOR,
                            "div.flatpickr-calendar.open .flatpickr-next-month"))
                    )
                    next_month_button.click()
                    await asyncio.sleep(1.5)
                else:
                    break

            except (TimeoutException, NoSuchElementException):
                await bot.send_message(chat_id=CHAT_ID, text="Չհաջողվեց գտնել ազատ օր 😕")
                break

        png_bytes = driver.get_screenshot_as_png()
        bio = io.BytesIO(png_bytes)
        bio.name = "screenshot_after_post.png"
        bio.seek(0)

        await bot.send_photo(chat_id=CHAT_ID, photo=InputFile(bio), caption="Screenshot after background request.")

    except Exception as e:
        await bot.send_message(chat_id=CHAT_ID, text=f"Error occurred: {e}")
    finally:
        driver.quit()


# Run check() directly
if __name__ == '__main__':
    asyncio.run(check())
