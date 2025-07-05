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
from selenium.common.exceptions import TimeoutException, NoSuchElementException, StaleElementReferenceException # Import StaleElementReferenceException
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

# Read from environment variables
TOKEN = os.getenv("TELEGRAM_TOKEN")
NUMBER1 = os.getenv("NUMBER1", "")
NUMBER2 = os.getenv("NUMBER2", "")

async def take_screenshot_and_reply(driver, update, caption_prefix=""):
    """Helper function to take screenshot and reply to Telegram."""
    try:
        screenshot_bytes = driver.get_screenshot_as_png()
        bio = io.BytesIO(screenshot_bytes)
        bio.name = "debug_screenshot.png"
        await update.message.reply_photo(photo=bio, caption=f"{caption_prefix} Screenshot at this stage.")
        print(f"Debug: Screenshot taken and sent for: {caption_prefix}")
    except Exception as e:
        print(f"Debug: Failed to take or send screenshot: {e}")
        await update.message.reply_text(f"Debug: Failed to capture screenshot: {e}")


async def check(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Opening Chrome...")
    print("Debug: Initiating check function...")

    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--window-size=1920,1180")
    # Optional: Add --disable-gpu if you continue to see obscure errors
    # chrome_options.add_argument("--disable-gpu")

    service = Service("/usr/bin/chromedriver")
    driver = webdriver.Chrome(service=service, options=chrome_options)

    try:
        print("Debug: Navigating to roadpolice.am...")
        driver.get("https://roadpolice.am/hy")
        await take_screenshot_and_reply(driver, update, "After navigating to URL")
        print(f"Debug: Current URL: {driver.current_url}")
        print(f"Debug: Current Title: {driver.title}")

        # Click button to open modal
        print("Debug: Waiting for initial button to be clickable...")
        button_span_selector = "#index_page_steps > div > div > div > div:nth-child(3) > button > span > span"
        button_span = WebDriverWait(driver, 20).until( # Increased timeout for robustness
            EC.element_to_be_clickable((By.CSS_SELECTOR, button_span_selector))
        )
        print("Debug: Initial button span found. Clicking button...")
        button = button_span.find_element(By.XPATH, "./ancestor::button")
        button.click()
        await take_screenshot_and_reply(driver, update, "After clicking initial button")
        print("Debug: Initial button clicked. Waiting for modal...")

        await asyncio.sleep(0.5) # Slight increase just in case

        print("Debug: Performing TAB actions...")
        actions = ActionChains(driver)
        actions.send_keys(Keys.TAB).pause(0.5).send_keys(Keys.TAB).perform() # Increased pause
        await take_screenshot_and_reply(driver, update, "After first TAB actions")

        await asyncio.sleep(1.5) # Slight increase
        active_element = driver.switch_to.active_element
        print(f"Debug: Active element after first TAB: {active_element.tag_name}, {active_element.get_attribute('outerHTML')[:100]}...")

        print("Debug: Entering NUMBER1...")
        for digit in NUMBER1:
            active_element.send_keys(digit)
            await asyncio.sleep(0.1) # Small sleep between digits
        await take_screenshot_and_reply(driver, update, "After entering NUMBER1")

        print("Debug: Performing second TAB action...")
        actions.send_keys(Keys.TAB).perform()
        await asyncio.sleep(0.5) # Slight increase

        active_element = driver.switch_to.active_element
        print(f"Debug: Active element after second TAB: {active_element.tag_name}, {active_element.get_attribute('outerHTML')[:100]}...")

        print("Debug: Entering NUMBER2...")
        for digit in NUMBER2:
            active_element.send_keys(digit)
            await asyncio.sleep(0.1)
        await take_screenshot_and_reply(driver, update, "After entering NUMBER2")

        print("Debug: Performing third TAB action...")
        actions.send_keys(Keys.TAB).perform()

        await asyncio.sleep(0.7) # Slight increase

        print("Debug: Waiting for submit button...")
        submit_button_selector = "#hqb-login-submit"
        submit_button = WebDriverWait(driver, 20).until( # Increased timeout
            EC.element_to_be_clickable((By.CSS_SELECTOR, submit_button_selector))
        )
        print("Debug: Submit button found. Clicking...")
        submit_button.click()
        await take_screenshot_and_reply(driver, update, "After clicking submit button")
        print("Debug: Submit button clicked. Waiting for page load...")

        await asyncio.sleep(2) # Increased sleep for page load

        # Click first dropdown
        print("Debug: Waiting for first dropdown...")
        dropdown_selector = "body > div > main > div.info-section.info-section--without-cover.pr > div > div > div.info-section__group-item.pr.license-hqb-register > form > div:nth-child(2) > span > span.selection > span"
        dropdown = WebDriverWait(driver, 20).until( # Increased timeout
            EC.element_to_be_clickable((By.CSS_SELECTOR, dropdown_selector))
        )
        print("Debug: First dropdown found. Clicking...")
        dropdown.click()
        await take_screenshot_and_reply(driver, update, "After clicking first dropdown")
        print("Debug: First dropdown clicked. Performing ARROW_DOWN...")

        await asyncio.sleep(0.5)
        actions = ActionChains(driver)
        actions.send_keys(Keys.ARROW_DOWN).pause(0.2) # Increased pause
        actions.send_keys(Keys.ARROW_DOWN).pause(0.2) # Increased pause
        actions.send_keys(Keys.ENTER).perform()
        await take_screenshot_and_reply(driver, update, "After selecting first dropdown option")
        print("Debug: First dropdown option selected.")

        await asyncio.sleep(1) # Increased sleep

        # Click second dropdown
        print("Debug: Waiting for second dropdown...")
        second_dropdown_selector = "body > div > main > div.info-section.info-section--without-cover.pr > div > div > div.info-section__group-item.pr.license-hqb-register > form > div:nth-child(3) > span > span.selection > span"
        second_dropdown = WebDriverWait(driver, 20).until( # Increased timeout
            EC.element_to_be_clickable((By.CSS_SELECTOR, second_dropdown_selector))
        )
        print("Debug: Second dropdown found. Clicking...")
        second_dropdown.click()
        await take_screenshot_and_reply(driver, update, "After clicking second dropdown")
        print("Debug: Second dropdown clicked. Performing ARROW_DOWN...")
        await asyncio.sleep(0.5)

        actions = ActionChains(driver)
        actions.send_keys(Keys.ARROW_DOWN).pause(0.2) # Increased pause
        actions.send_keys(Keys.ARROW_DOWN).pause(0.2) # Increased pause
        actions.send_keys(Keys.ENTER).perform()
        await take_screenshot_and_reply(driver, update, "After selecting second dropdown option")
        print("Debug: Second dropdown option selected.")

        await asyncio.sleep(2) # Increased sleep

        print("Debug: Waiting for calendar label...")
        calendar_label_selector = "body > div.wrapper > main > div.info-section.info-section--without-cover.pr > div > div > div.info-section__group-item.pr.license-hqb-register > form > div:nth-child(4) > label"
        calendar_label = WebDriverWait(driver, 20).until( # Increased timeout
            EC.element_to_be_clickable((By.CSS_SELECTOR, calendar_label_selector))
        )
        print("Debug: Calendar label found. Clicking...")
        calendar_label.click()
        await take_screenshot_and_reply(driver, update, "After clicking calendar label")
        print("Debug: Calendar opened.")
        await asyncio.sleep(1) # Increased sleep

        while True:
            try:
                print("Debug: Checking for dayContainer in calendar...")
                day_container = WebDriverWait(driver, 10).until( # Increased timeout
                    EC.presence_of_element_located(
                        (By.CSS_SELECTOR, "div.flatpickr-calendar.open .flatpickr-days .dayContainer")
                    )
                )
                days = day_container.find_elements(By.CSS_SELECTOR, "span")
                print(f"Debug: Found {len(days)} days in calendar.")

                found_next_month_day = False
                found_valid_day = False

                for day_index, day in enumerate(days):
                    classes = day.get_attribute("class") or ""
                    print(f"Debug: Processing day {day_index}: text='{day.text}', class='{classes}'")

                    if "flatpickr-disabled" in classes or "prevMonthDay" in classes:
                        print(f"Debug: Day {day.text} is disabled or previous month. Skipping.")
                        continue

                    elif "nextMonthDay" in classes:
                        print(f"Debug: Day {day.text} is next month day. Will try next month.")
                        found_next_month_day = True
                        break # Break from inner loop, need to go to next month

                    else:
                        try:
                            aria_label = day.get_attribute("aria-label")
                            print(f"Debug: Found an interactable day: {aria_label}. Clicking...")
                            day.click()
                            found_valid_day = True
                            await asyncio.sleep(5) # Increased sleep significantly for post-click processing
                            await take_screenshot_and_reply(driver, update, f"After clicking day: {aria_label}")

                            # This is where your successful reply happens, so ensure it gets called
                            await update.message.reply_photo(
                                photo=io.BytesIO(driver.get_screenshot_as_png()), # Take fresh screenshot here
                                caption=f"Առաջին հասանելի օրն է՝ {aria_label}"
                            )
                            print(f"Debug: Replied with available day: {aria_label}")
                            return # Exit the function on success
                        except StaleElementReferenceException:
                            print("Debug: Stale element reference while clicking day. Retrying loop.")
                            break # Break inner loop to re-find elements
                        except Exception as e:
                            print(f"Debug: Error clicking day {day.text}: {e}")
                            await update.message.reply_text(f"Debug: Error clicking day {day.text}: {e}")
                            break # Break inner loop, might need to retry month or exit

                if found_next_month_day:
                    print("Debug: Moving to next month...")
                    next_month_button = WebDriverWait(driver, 10).until( # Increased timeout
                        EC.element_to_be_clickable(
                            (By.CSS_SELECTOR, "div.flatpickr-calendar.open .flatpickr-next-month")
                        )
                    )
                    next_month_button.click()
                    await take_screenshot_and_reply(driver, update, "After clicking next month button")
                    await asyncio.sleep(2) # Increased sleep
                elif not found_valid_day: # If no valid day found and not next month
                    print("Debug: No valid days found in current month and not moving to next month.")
                    break # Exit while loop if no more options
                # If found_valid_day is True, the function would have returned already.

            except (TimeoutException, NoSuchElementException) as e:
                print(f"Debug: Calendar navigation error: {e}")
                await update.message.reply_text("Չհաջողվեց գտնել ազատ օր 😕 (Error in calendar logic)")
                break # Exit the while loop on error

        # Final screenshot if a day wasn't found or an error occurred before returning
        print("Debug: Reached end of calendar loop or error. Taking final screenshot.")
        png_bytes = driver.get_screenshot_as_png()
        bio = io.BytesIO(png_bytes)
        bio.name = "screenshot_final.png" # Changed name to avoid confusion
        await update.message.reply_photo(photo=bio, caption="Screenshot at end of process.")

    except TimeoutException as e:
        error_message = f"Timeout error: {e}. An element was not found in time. Current URL: {driver.current_url}"
        print(f"Debug: {error_message}")
        await update.message.reply_text(f"🚧 Timeout error: An element was not found. Please check logs. 🚧")
        await take_screenshot_and_reply(driver, update, "On TimeoutException")
    except NoSuchElementException as e:
        error_message = f"Element not found error: {e}. Current URL: {driver.current_url}"
        print(f"Debug: {error_message}")
        await update.message.reply_text(f"🚨 Element not found: A required part of the page was missing. Check logs. 🚨")
        await take_screenshot_and_reply(driver, update, "On NoSuchElementException")
    except StaleElementReferenceException as e:
        error_message = f"Stale element error: {e}. Element became detached from DOM. Current URL: {driver.current_url}"
        print(f"Debug: {error_message}")
        await update.message.reply_text(f"👻 Stale element error: The page changed unexpectedly. Check logs. 👻")
        await take_screenshot_and_reply(driver, update, "On StaleElementReferenceException")
    except Exception as e:
        error_message = f"An unexpected error occurred: {e}. Current URL: {driver.current_url}"
        print(f"Debug: {error_message}")
        await update.message.reply_text(f"🛑 Error occurred: {e} 🛑")
        try:
            await take_screenshot_and_reply(driver, update, "On General Exception")
        except:
            pass # Avoid erroring out on screenshot if driver is completely broken
    finally:
        print("Debug: Quitting driver...")
        driver.quit()
        print("Debug: Driver quit.")


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Hello! I'm your bot.")

if __name__ == '__main__':
    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("check", check))

    print("Bot is running...")
    app.run_polling()
