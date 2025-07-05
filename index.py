import io
import os
import asyncio
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.action_chains import ActionChains
from selenium.common.exceptions import TimeoutException, NoSuchElementException, StaleElementReferenceException
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

# Read from environment variables
TOKEN = os.getenv("TELEGRAM_TOKEN")
NUMBER1 = os.getenv("NUMBER1", "")
NUMBER2 = os.getenv("NUMBER2", "")

async def check(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Opening Chrome...")

    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--window-size=1920,1180")
    # Optional: If you added --disable-gpu for stability and it helped, you can keep it.
    # chrome_options.add_argument("--disable-gpu")

    service = Service("/usr/bin/chromedriver")
    driver = webdriver.Chrome(service=service, options=chrome_options)

    try:
        driver.get("https://roadpolice.am/hy")

        # Click button to open modal
        button_span = WebDriverWait(driver, 20).until( # Kept increased timeout
            EC.element_to_be_clickable(
                (By.CSS_SELECTOR,
                 "#index_page_steps > div > div > div > div:nth-child(3) > button > span > span")
            )
        )
        button = button_span.find_element(By.XPATH, "./ancestor::button")
        button.click()

        await asyncio.sleep(0.5) # Kept slight increase

        actions = ActionChains(driver)
        actions.send_keys(Keys.TAB).pause(0.5).send_keys(Keys.TAB).perform() # Kept increased pause

        await asyncio.sleep(1.5) # Kept slight increase
        active_element = driver.switch_to.active_element

        for digit in NUMBER1:
            active_element.send_keys(digit)
            await asyncio.sleep(0.1)

        actions.send_keys(Keys.TAB).perform()
        await asyncio.sleep(0.5) # Kept slight increase

        active_element = driver.switch_to.active_element
        for digit in NUMBER2:
            active_element.send_keys(digit)
            await asyncio.sleep(0.1)

        actions.send_keys(Keys.TAB).perform()

        await asyncio.sleep(0.7) # Kept slight increase
        submit_button = WebDriverWait(driver, 20).until( # Kept increased timeout
            EC.element_to_be_clickable((By.CSS_SELECTOR, "#hqb-login-submit"))
        )
        submit_button.click()

        await asyncio.sleep(2) # Kept increased sleep

        # Click first dropdown
        dropdown = WebDriverWait(driver, 20).until( # Kept increased timeout
            EC.element_to_be_clickable(
                (By.CSS_SELECTOR,
                 "body > div > main > div.info-section.info-section--without-cover.pr > div > div > div.info-section__group-item.pr.license-hqb-register > form > div:nth-child(2) > span > span.selection > span")
            )
        )
        dropdown.click()

        await asyncio.sleep(0.5) # Kept slight increase
        actions = ActionChains(driver)
        actions.send_keys(Keys.ARROW_DOWN).pause(0.2) # Kept increased pause
        actions.send_keys(Keys.ARROW_DOWN).pause(0.2) # Kept increased pause
        actions.send_keys(Keys.ENTER).perform()

        await asyncio.sleep(1) # Kept slight increase

        # Click second dropdown
        second_dropdown = WebDriverWait(driver, 20).until( # Kept increased timeout
            EC.element_to_be_clickable(
                (By.CSS_SELECTOR,
                 "body > div > main > div.info-section.info-section--without-cover.pr > div > div > div.info-section__group-item.pr.license-hqb-register > form > div:nth-child(3) > span > span.selection > span")
            )
        )
        second_dropdown.click()
        await asyncio.sleep(0.5) # Kept slight increase

        actions = ActionChains(driver)
        actions.send_keys(Keys.ARROW_DOWN).pause(0.2) # Kept increased pause
        actions.send_keys(Keys.ARROW_DOWN).pause(0.2) # Kept increased pause
        actions.send_keys(Keys.ENTER).perform()

        await asyncio.sleep(2) # Kept increased sleep

        calendar_label = WebDriverWait(driver, 20).until( # Kept increased timeout
            EC.element_to_be_clickable(
                (By.CSS_SELECTOR,
                 "body > div.wrapper > main > div.info-section.info-section--without-cover.pr > div > div > div.info-section__group-item.pr.license-hqb-register > form > div:nth-child(4) > label")
            )
        )
        calendar_label.click()
        await asyncio.sleep(1) # Kept slight increase

        while True:
            try:
                day_container = WebDriverWait(driver, 10).until( # Kept increased timeout
                    EC.presence_of_element_located(
                        (By.CSS_SELECTOR, "div.flatpickr-calendar.open .flatpickr-days .dayContainer")
                    )
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
                        await asyncio.sleep(5) # Kept increased sleep significantly for post-click processing
                        screenshot = driver.get_screenshot_as_png()
                        bio = io.BytesIO(screenshot)
                        bio.name = "valid_date.png"

                        await update.message.reply_photo(
                            photo=bio,
                            caption=f"Առաջին հասանելի օրն է՝ {aria_label}"
                        )
                        return

                if found_next_month_day:
                    next_month_button = WebDriverWait(driver, 10).until( # Kept increased timeout
                        EC.element_to_be_clickable(
                            (By.CSS_SELECTOR, "div.flatpickr-calendar.open .flatpickr-next-month")
                        )
                    )
                    next_month_button.click()
                    await asyncio.sleep(2) # Kept increased sleep
                else:
                    break

            except (TimeoutException, NoSuchElementException, StaleElementReferenceException):
                await update.message.reply_text("Չհաջողվեց գտնել ազատ օր 😕")
                break

        # Final screenshot (if a valid day wasn't found or an error occurred before returning)
        png_bytes = driver.get_screenshot_as_png()
        bio = io.BytesIO(png_bytes)
        bio.name = "screenshot_after_post.png"

        await update.message.reply_photo(photo=bio, caption="Screenshot after background request.")

    except Exception as e:
        # Keep general error handling for unexpected issues
        await update.message.reply_text(f"Error occurred: {e}")

    finally:
        driver.quit()

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Hello! I'm your bot.")

if __name__ == '__main__':
    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("check", check))

    print("Bot is running...")
    app.run_polling()
