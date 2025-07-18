import io
import os
import asyncio
import sys # Import sys to access command-line arguments

from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.action_chains import ActionChains
from selenium.common.exceptions import TimeoutException, NoSuchElementException, StaleElementReferenceException
from telegram import Update, Bot # Import Bot
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

# Read from environment variables
TOKEN = os.getenv("TELEGRAM_TOKEN")
NUMBER1 = os.getenv("NUMBER1", "")
NUMBER2 = os.getenv("NUMBER2", "")

# Define a placeholder for update and context for scheduled runs
class ScheduledUpdate:
    def __init__(self, bot_instance, chat_id):
        self.effective_chat = type('obj', (object,), {'id' : chat_id})() # Mock effective_chat
        self.message = self._MockMessage(bot_instance, chat_id) # Instantiate the mock message

    class _MockMessage: # Define a nested class for the mock message
        def __init__(self, bot_instance, chat_id):
            self.bot_instance = bot_instance
            self.chat_id = chat_id

        async def reply_text(self, text, **kwargs):
            """Mocks the reply_text method for scheduled runs."""
            # Use bot_instance to send the message
            await self.bot_instance.send_message(chat_id=self.chat_id, text=text, **kwargs)

        async def reply_photo(self, photo, caption=None, **kwargs):
            """Mocks the reply_photo method for scheduled runs."""
            # Use bot_instance to send the photo
            await self.bot_instance.send_photo(chat_id=self.chat_id, photo=photo, caption=caption, **kwargs)

class ScheduledContext:
    # This might need to be more elaborate depending on what your handlers expect from context
    pass


async def check(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # This block is used for both manual commands and scheduled runs
    if update: # Check if it's a regular Telegram update
        await update.message.reply_text("Opening Chrome...")
    else: # This is for scheduled runs where `update` is mocked
        scheduled_chat_id = os.getenv("TELEGRAM_SCHEDULE_CHAT_ID")
        if scheduled_chat_id:
            # We already have a bot_instance in ScheduledUpdate, so no need to create a new one here.
            # The mocked reply_text will use the bot_instance provided to ScheduledUpdate.
            # This line will now call the mocked reply_text
            await update.message.reply_text("[Scheduled Check] Opening Chrome...")
        else:
            print("Warning: TELEGRAM_SCHEDULE_CHAT_ID not set for scheduled run.")


    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--window-size=1920,1180")

    service = Service("/usr/bin/chromedriver")
    driver = webdriver.Chrome(service=service, options=chrome_options)

    try:
        driver.get("https://roadpolice.am/hy")
        await asyncio.sleep(2) 
        button_span = WebDriverWait(driver, 20).until(
            EC.element_to_be_clickable(
                (By.CSS_SELECTOR,
                 "#index_page_steps > div > div > div > div:nth-child(3) > button > span > span")
            )
        )
        button = button_span.find_element(By.XPATH, "./ancestor::button")
        button.click()

        await asyncio.sleep(0.5)

        actions = ActionChains(driver)
        actions.send_keys(Keys.TAB).pause(0.5).send_keys(Keys.TAB).perform()

        await asyncio.sleep(1.5)
        active_element = driver.switch_to.active_element

        for digit in NUMBER1:
            active_element.send_keys(digit)
            await asyncio.sleep(0.1)

        actions.send_keys(Keys.TAB).perform()
        await asyncio.sleep(0.5)

        active_element = driver.switch_to.active_element
        for digit in NUMBER2:
            active_element.send_keys(digit)
            await asyncio.sleep(0.1)

        actions.send_keys(Keys.TAB).perform()

        await asyncio.sleep(0.7)
        submit_button = WebDriverWait(driver, 20).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, "#hqb-login-submit"))
        )
        submit_button.click()

        await asyncio.sleep(2)

        dropdown = WebDriverWait(driver, 20).until(
            EC.element_to_be_clickable(
                (By.CSS_SELECTOR,
                 "body > div > main > div.info-section.info-section--without-cover.pr > div > div > div.info-section__group-item.pr.license-hqb-register > form > div:nth-child(2) > span > span.selection > span")
            )
        )
        dropdown.click()

        await asyncio.sleep(0.5)
        actions = ActionChains(driver)
        actions.send_keys(Keys.ARROW_DOWN).pause(0.2)
        actions.send_keys(Keys.ARROW_DOWN).pause(0.2)
        actions.send_keys(Keys.ENTER).perform()

        await asyncio.sleep(1.5)

        second_dropdown = WebDriverWait(driver, 20).until(
            EC.element_to_be_clickable(
                (By.CSS_SELECTOR,
                 "body > div > main > div.info-section.info-section--without-cover.pr > div > div > div.info-section__group-item.pr.license-hqb-register > form > div:nth-child(3) > span > span.selection > span")
            )
        )
        second_dropdown.click()
        await asyncio.sleep(0.5)

        actions = ActionChains(driver)
        actions.send_keys(Keys.ARROW_DOWN).pause(0.2)
        actions.send_keys(Keys.ARROW_DOWN).pause(0.2)
        actions.send_keys(Keys.ENTER).perform()

        await asyncio.sleep(5)

        calendar_label = WebDriverWait(driver, 20).until(
            EC.element_to_be_clickable(
                (By.CSS_SELECTOR,
                 "body > div.wrapper > main > div.info-section.info-section--without-cover.pr > div > div > div.info-section__group-item.pr.license-hqb-register > form > div:nth-child(4) > label")
            )
        )
        calendar_label.click()
        await asyncio.sleep(2)

        while True:
            try:
                day_container = WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located(
                        (By.CSS_SELECTOR, "div.flatpickr-calendar.open .flatpickr-days .dayContainer")
                    )
                )
                days = day_container.find_elements(By.CSS_SELECTOR, "span")

                found_next_month_day = False

                for day in days:
                    classes = day.get_attribute("class") or ""

                    if "flatpickr-disabled" in classes:
                        continue

                    # elif "nextMonthDay" in classes:
                    #     found_next_month_day = True
                    #     break

                    else:
                        # aria_label = day.get_attribute("aria-label")
                        day.click()
                        await asyncio.sleep(5)
                        closest = WebDriverWait(driver, 10).until(
                                    EC.element_to_be_clickable((By.CSS_SELECTOR, "#nearest-day-submit"))
                                )
                        closest.click()
                        await asyncio.sleep(8)
                        screenshot = driver.get_screenshot_as_png()
                        bio = io.BytesIO(screenshot)
                        bio.name = "valid_date.png"

                        if update:
                            await update.message.reply_photo(
                                photo=bio,
                                caption=f"Առաջին հասանելի օրն է՝"
                            )
                        else:
                            # This now uses the mocked reply_photo method provided by ScheduledUpdate
                            await update.message.reply_photo(
                                photo=bio,
                                caption=f"[Scheduled] Առաջին հասանելի օրն է՝"
                            )
                        return

                if found_next_month_day:
                    next_month_button = WebDriverWait(driver, 10).until(
                        EC.element_to_be_clickable(
                            (By.CSS_SELECTOR, "div.flatpickr-calendar.open .flatpickr-next-month")
                        )
                    )
                    next_month_button.click()
                    await asyncio.sleep(2)
                else:
                    break

            except (TimeoutException, NoSuchElementException, StaleElementReferenceException):
                if update:
                    await update.message.reply_text("Չհաջողվեց գտնել ազատ օր 😕")
                else:
                    # This now uses the mocked reply_text method provided by ScheduledUpdate
                    await update.message.reply_text("[Scheduled] Չհաջողվեց գտնել ազատ օր 😕")
                break

        png_bytes = driver.get_screenshot_as_png()
        bio = io.BytesIO(png_bytes)
        bio.name = "screenshot_after_post.png"

        if update:
            await update.message.reply_photo(photo=bio, caption="Screenshot after background request.")
        else:
            # This now uses the mocked reply_photo method provided by ScheduledUpdate
            await update.message.reply_photo(photo=bio, caption="[Scheduled] Screenshot after background request.")


    except Exception as e:
        error_message = f"Error occurred: {e}"
        if update:
            await update.message.reply_text(error_message)
        else:
            # This now uses the mocked reply_text method provided by ScheduledUpdate
            await update.message.reply_text(f"[Scheduled] {error_message}")


    finally:
        driver.quit()

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Hello! I'm your bot.")

async def run_scheduled_check():
    """Function to run check for scheduled events."""
    scheduled_chat_id = os.getenv("TELEGRAM_SCHEDULE_CHAT_ID")
    if not scheduled_chat_id:
        print("Error: TELEGRAM_SCHEDULE_CHAT_ID environment variable is not set. Cannot send scheduled messages.")
        return

    bot_instance = Bot(TOKEN) # Create a single bot instance for this scheduled run
    mock_update = ScheduledUpdate(bot_instance, scheduled_chat_id)
    mock_context = ScheduledContext()

    await check(mock_update, mock_context)


if __name__ == '__main__':
    if "--scheduled-check" in sys.argv:
        print("Running scheduled check...")
        asyncio.run(run_scheduled_check())
    else:
        app = ApplicationBuilder().token(TOKEN).build()

        app.add_handler(CommandHandler("start", start))
        app.add_handler(CommandHandler("check", check))

        print("Bot is running in polling mode...")
        app.run_polling()
