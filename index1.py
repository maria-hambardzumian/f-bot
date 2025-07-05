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
        self.message = type('obj', (object,), {'reply_text' : lambda text: asyncio.create_task(bot_instance.send_message(chat_id=chat_id, text=text)),
                                                'reply_photo' : lambda photo, caption: asyncio.create_task(bot_instance.send_photo(chat_id=chat_id, photo=photo, caption=caption))
                                               })()

class ScheduledContext:
    # This might need to be more elaborate depending on what your handlers expect from context
    pass


async def check(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # This block is used for both manual commands and scheduled runs
    if update: # Check if it's a regular Telegram update
        await update.message.reply_text("Opening Chrome...")
    else: # This is for scheduled runs where `update` is mocked
        # You'll need a way to get the chat_id for scheduled messages
        # For simplicity, let's assume you've set a chat ID as an environment variable
        scheduled_chat_id = os.getenv("TELEGRAM_SCHEDULE_CHAT_ID")
        if scheduled_chat_id:
            await Bot(TOKEN).send_message(chat_id=scheduled_chat_id, text="[Scheduled Check] Opening Chrome...")
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

        await asyncio.sleep(1)

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

        await asyncio.sleep(2)

        calendar_label = WebDriverWait(driver, 20).until(
            EC.element_to_be_clickable(
                (By.CSS_SELECTOR,
                 "body > div.wrapper > main > div.info-section.info-section--without-cover.pr > div > div > div.info-section__group-item.pr.license-hqb-register > form > div:nth-child(4) > label")
            )
        )
        calendar_label.click()
        await asyncio.sleep(1)

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

                    if "flatpickr-disabled" in classes or "prevMonthDay" in classes:
                        continue

                    elif "nextMonthDay" in classes:
                        found_next_month_day = True
                        break

                    else:
                        aria_label = day.get_attribute("aria-label")
                        day.click()
                        await asyncio.sleep(5)
                        screenshot = driver.get_screenshot_as_png()
                        bio = io.BytesIO(screenshot)
                        bio.name = "valid_date.png"

                        if update: # Reply to specific update if it's a command
                            await update.message.reply_photo(
                                photo=bio,
                                caption=f"Առաջին հասանելի օրն է՝ {aria_label}"
                            )
                        else: # Send to scheduled chat ID if it's a scheduled run
                            scheduled_chat_id = os.getenv("TELEGRAM_SCHEDULE_CHAT_ID")
                            if scheduled_chat_id:
                                bot_instance = Bot(TOKEN)
                                await bot_instance.send_photo(chat_id=scheduled_chat_id, photo=bio, caption=f"[Scheduled] Առաջին հասանելի օրն է՝ {aria_label}")
                            else:
                                print(f"Warning: No chat ID for scheduled photo reply for {aria_label}.")
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
                    scheduled_chat_id = os.getenv("TELEGRAM_SCHEDULE_CHAT_ID")
                    if scheduled_chat_id:
                        bot_instance = Bot(TOKEN)
                        await bot_instance.send_message(chat_id=scheduled_chat_id, text="[Scheduled] Չհաջողվեց գտնել ազատ օր 😕")
                    else:
                        print("Warning: No chat ID for scheduled failure message.")
                break

        png_bytes = driver.get_screenshot_as_png()
        bio = io.BytesIO(png_bytes)
        bio.name = "screenshot_after_post.png"

        if update:
            await update.message.reply_photo(photo=bio, caption="Screenshot after background request.")
        else:
            scheduled_chat_id = os.getenv("TELEGRAM_SCHEDULE_CHAT_ID")
            if scheduled_chat_id:
                bot_instance = Bot(TOKEN)
                await bot_instance.send_photo(chat_id=scheduled_chat_id, photo=bio, caption="[Scheduled] Screenshot after background request.")


    except Exception as e:
        error_message = f"Error occurred: {e}"
        if update:
            await update.message.reply_text(error_message)
        else:
            scheduled_chat_id = os.getenv("TELEGRAM_SCHEDULE_CHAT_ID")
            if scheduled_chat_id:
                bot_instance = Bot(TOKEN)
                await bot_instance.send_message(chat_id=scheduled_chat_id, text=f"[Scheduled] {error_message}")
            else:
                print(f"Warning: No chat ID for scheduled error message: {error_message}")


    finally:
        driver.quit()

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Hello! I'm your bot.")

async def run_scheduled_check():
    """Function to run check for scheduled events."""
    # Create mock update and context for scheduled runs
    # You NEED to set TELEGRAM_SCHEDULE_CHAT_ID as a GitHub Secret/Env Var
    scheduled_chat_id = os.getenv("TELEGRAM_SCHEDULE_CHAT_ID")
    if not scheduled_chat_id:
        print("Error: TELEGRAM_SCHEDULE_CHAT_ID environment variable is not set. Cannot send scheduled messages.")
        return

    # Initialize a temporary bot instance to send messages for scheduled runs
    # This uses a simple Bot object to send messages without the full Application.
    # This assumes the bot token is available.
    bot_instance = Bot(TOKEN)

    # Create mock update and context objects
    mock_update = ScheduledUpdate(bot_instance, scheduled_chat_id)
    mock_context = ScheduledContext() # No specific context needed for this use case

    await check(mock_update, mock_context)


if __name__ == '__main__':
    # Check for a specific argument to decide if it's a scheduled run
    if "--scheduled-check" in sys.argv:
        print("Running scheduled check...")
        asyncio.run(run_scheduled_check())
    else:
        # Normal Telegram bot polling for interactive commands
        app = ApplicationBuilder().token(TOKEN).build()

        app.add_handler(CommandHandler("start", start))
        app.add_handler(CommandHandler("check", check))

        print("Bot is running in polling mode...")
        app.run_polling()
