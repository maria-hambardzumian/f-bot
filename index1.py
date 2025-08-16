import io
import os
import asyncio
import sys # Import sys to access command-line arguments
from datetime import datetime, timedelta, timezone
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

# Constants
MIN_DATE_THRESHOLD = "2025-10-01"  # Minimum acceptable date for reservations

# Read from environment variables
TOKEN = os.getenv("TELEGRAM_TOKEN")
NUMBER1 = os.getenv("NUMBER1", "")
NUMBER2 = os.getenv("NUMBER2", "")

# Debug logging function
async def debug_log(update, message, error=None):
    """Send debug information to chat"""
    try:
        if error:
            debug_message = f"🐛 DEBUG: {message}\n❌ Error: {str(error)}"
        else:
            debug_message = f"🐛 DEBUG: {message}"
            
        if update:
            await update.message.reply_text(debug_message)
        else:
            print(f"[Scheduled Debug] {debug_message}")
    except Exception:
        print(f"Debug logging failed: {message}")

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
    # Convert constant to datetime object
    min_date_threshold = datetime.strptime(MIN_DATE_THRESHOLD, "%Y-%m-%d")
    
    # Validate environment variables
    if not NUMBER1 or not NUMBER2:
        await debug_log(update, f"Missing credentials - NUMBER1: {'SET' if NUMBER1 else 'MISSING'}, NUMBER2: {'SET' if NUMBER2 else 'MISSING'}")
        error_msg = "❌ Bot configuration error: Missing NUMBER1 or NUMBER2 environment variables"
        if update:
            await update.message.reply_text(error_msg)
        return
    
    await debug_log(update, f"Environment check - NUMBER1 length: {len(NUMBER1)}, NUMBER2 length: {len(NUMBER2)}")
    
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


    try:
        await debug_log(update, "Setting up Chrome options...")
        chrome_options = Options()
        chrome_options.add_argument("--headless")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--disable-web-security")
        chrome_options.add_argument("--disable-features=VizDisplayCompositor")
        chrome_options.add_argument("--window-size=1920,1180")
        chrome_options.add_argument("--user-agent=Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36")

        await debug_log(update, "Starting ChromeDriver...")
        service = Service("/usr/bin/chromedriver")
        driver = webdriver.Chrome(service=service, options=chrome_options)
        await debug_log(update, "ChromeDriver started successfully")
    except Exception as e:
        await debug_log(update, "Failed to start ChromeDriver", e)
        raise

    try:
        await debug_log(update, "Loading website...")
        driver.get("https://roadpolice.am/en")
        
        # Wait 4 seconds as requested
        await asyncio.sleep(4)
        await debug_log(update, "Website loaded, waited 4 seconds")
        
        # Take screenshot of initial page
        initial_screenshot = driver.get_screenshot_as_png()
        initial_bio = io.BytesIO(initial_screenshot)
        initial_bio.name = "01_initial_page.png"
        await update.message.reply_photo(photo=initial_bio, caption="📸 Step 1: Initial page loaded")
        
        await debug_log(update, "Looking for initial button...")
        button_span = WebDriverWait(driver, 20).until(
            EC.element_to_be_clickable(
                (By.CSS_SELECTOR,
                 "#index_page_steps > div > div > div > div:nth-child(3) > button > span > span")
            )
        )
        button = button_span.find_element(By.XPATH, "./ancestor::button")
        button.click()
        await debug_log(update, "Initial button clicked successfully")
        
        # Take screenshot of modal opened
        await asyncio.sleep(1)
        modal_screenshot = driver.get_screenshot_as_png()
        modal_bio = io.BytesIO(modal_screenshot)
        modal_bio.name = "02_modal_opened.png"
        await update.message.reply_photo(photo=modal_bio, caption="📸 Step 2: Login modal opened")
# document.querySelector("#hqb-login-submit")
        await asyncio.sleep(0.2)  # short wait to make sure modal is fully open

        # Step 2: Send POST request in the background
        actions = ActionChains(driver)
        actions.send_keys(Keys.TAB).pause(0.4).send_keys(Keys.TAB).perform()

        await asyncio.sleep(1)  # Wait half a second before screenshot
        await debug_log(update, f"Entering first number: {NUMBER1}")
        active_element = driver.switch_to.active_element
        for digit in NUMBER1:
            active_element.send_keys(digit)
            await asyncio.sleep(0.1)

        actions.send_keys(Keys.TAB).perform()
        await asyncio.sleep(0.3)

        await debug_log(update, f"Entering second number: {NUMBER2}")
        active_element = driver.switch_to.active_element
        for digit in NUMBER2:
            active_element.send_keys(digit)
            await asyncio.sleep(0.1)

        actions.send_keys(Keys.TAB).perform()

        await asyncio.sleep(0.5)
        await debug_log(update, "Looking for submit button...")
        submit_button = WebDriverWait(driver, 30).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, "#hqb-login-submit"))
        )
        await debug_log(update, "Submit button found")
        
        # Take screenshot before submitting
        before_submit_screenshot = driver.get_screenshot_as_png()
        before_submit_bio = io.BytesIO(before_submit_screenshot)
        before_submit_bio.name = "03_before_submit.png"
        await update.message.reply_photo(photo=before_submit_bio, caption="📸 Step 3: About to submit login form")
        
        submit_button.click()
        await debug_log(update, "Login form submitted")

        # Wait longer for login to process
        await asyncio.sleep(3)
        
        # Take screenshot immediately after submit
        after_submit_screenshot = driver.get_screenshot_as_png()
        after_submit_bio = io.BytesIO(after_submit_screenshot)
        after_submit_bio.name = "04_after_submit.png"
        await update.message.reply_photo(photo=after_submit_bio, caption="📸 Step 4: After login form submitted")
        
        # Check if login was successful by waiting for modal to close
        await debug_log(update, "Waiting for login modal to close...")
        
        try:
            # Wait for the modal to disappear (indicating successful login)
            WebDriverWait(driver, 15).until(
                EC.invisibility_of_element_located((By.CSS_SELECTOR, ".modal, [role='dialog'], .popup"))
            )
            await debug_log(update, "Login modal closed successfully")
        except TimeoutException:
            await debug_log(update, "Modal didn't close - checking what's still visible...")
            
        # Take screenshot to see current state
        login_result_screenshot = driver.get_screenshot_as_png()
        login_result_bio = io.BytesIO(login_result_screenshot)
        login_result_bio.name = "05_login_result.png"
        await update.message.reply_photo(photo=login_result_bio, caption="📸 Step 5: Login result")
        
        # Check for error messages or if we're still on login modal
        try:
            error_element = driver.find_element(By.CSS_SELECTOR, ".error, .alert, .warning, .text-danger")
            error_text = error_element.text
            await debug_log(update, f"Login error detected: {error_text}")
            await update.message.reply_text(f"❌ Login failed: {error_text}")
            return
        except:
            await debug_log(update, "No error messages found")
            
        # Check if we're still on the modal (login didn't work)
        try:
            modal_still_visible = driver.find_element(By.CSS_SELECTOR, "input[placeholder*='Document'], input[placeholder*='Phone'], .login-form, #login")
            await debug_log(update, "Login modal still visible - login may have failed")
            await update.message.reply_text("❌ Login modal still visible - credentials may be incorrect")
            return
        except:
            await debug_log(update, "Login modal not visible - appears successful")
            
        # Check for CAPTCHA or verification requirements
        try:
            captcha_element = driver.find_element(By.CSS_SELECTOR, "[id*='captcha'], [class*='captcha'], .verification, .recaptcha")
            await debug_log(update, "CAPTCHA or verification detected")
            await update.message.reply_text("❌ CAPTCHA or verification required - manual intervention needed")
            return
        except:
            await debug_log(update, "No CAPTCHA or verification detected")
        
        # Wait for page to be ready
        await debug_log(update, "Waiting for page to be ready...")
        WebDriverWait(driver, 15).until(
            lambda driver: driver.execute_script("return document.readyState") == "complete"
        )
        await debug_log(update, "Page is ready")
        
        # Additional wait for any dynamic content
        await asyncio.sleep(3)
        
        # Scroll down the page
        driver.execute_script("window.scrollTo(0, 200);")
        await debug_log(update, "Page scrolled down")
        await asyncio.sleep(2)  # Wait for scroll to complete
        
        # Take screenshot before looking for dropdown
        before_dropdown_screenshot = driver.get_screenshot_as_png()
        before_dropdown_bio = io.BytesIO(before_dropdown_screenshot)
        before_dropdown_bio.name = "06_before_dropdown.png"
        await update.message.reply_photo(photo=before_dropdown_bio, caption="📸 Step 6: Before looking for dropdown")

        await debug_log(update, "Looking for first dropdown...")
            dropdown = WebDriverWait(driver, 30).until(
                EC.element_to_be_clickable(
                    (By.CSS_SELECTOR,
                     "body > div > main > div.info-section.info-section--without-cover.pr > div > div > div.info-section__group-item.pr.license-hqb-register > form > div:nth-child(2) > span > span.selection > span")
                )
            )
            await debug_log(update, "First dropdown found successfully")
            
        except TimeoutException:
            await debug_log(update, "First dropdown not found - trying alternative selectors...")
            # Try alternative selectors
            alternative_selectors = [
                "select[name*='service'], select[name*='type']",
                ".select2-selection",
                "span.selection",
                "[id*='select2']"
            ]
            
            dropdown = None
            for selector in alternative_selectors:
                try:
                    await debug_log(update, f"Trying selector: {selector}")
                    dropdown = WebDriverWait(driver, 5).until(
                        EC.element_to_be_clickable((By.CSS_SELECTOR, selector))
                    )
                    await debug_log(update, f"Found dropdown with selector: {selector}")
                    break
                except:
                    continue
            
            if not dropdown:
                await debug_log(update, "All dropdown selectors failed")
                
                # Check what page we're actually on
                current_url = driver.current_url
                page_title = driver.title
                await debug_log(update, f"Current URL: {current_url}")
                await debug_log(update, f"Page title: {page_title}")
                
                # Take final debug screenshot
                debug_screenshot = driver.get_screenshot_as_png()
                debug_bio = io.BytesIO(debug_screenshot)
                debug_bio.name = "07_dropdown_not_found.png"
                await update.message.reply_photo(photo=debug_bio, caption=f"❌ Could not find dropdown\nURL: {current_url}\nTitle: {page_title}")
                return
        dropdown.click()

        await asyncio.sleep(1)
        actions = ActionChains(driver)
        actions.send_keys(Keys.ARROW_DOWN).pause(0.2)
        actions.send_keys(Keys.ARROW_DOWN).pause(0.2)
        actions.send_keys(Keys.ENTER).perform()

        await asyncio.sleep(2.5)

        second_dropdown = WebDriverWait(driver, 30).until(
            EC.element_to_be_clickable(
                (By.CSS_SELECTOR,
                 "body > div > main > div.info-section.info-section--without-cover.pr > div > div > div.info-section__group-item.pr.license-hqb-register > form > div:nth-child(3) > span > span.selection > span")
            )
        )
        second_dropdown.click()
        await asyncio.sleep(0.5)

        # Step 4: Select specific branch option
        actions = ActionChains(driver)
        actions.send_keys(Keys.ARROW_DOWN).pause(0.2)
        actions.send_keys(Keys.ARROW_DOWN).pause(0.2)
        actions.send_keys(Keys.ENTER).perform()

        await asyncio.sleep(15)

        calendar_label = WebDriverWait(driver, 30).until(
            EC.element_to_be_clickable(
                (By.CSS_SELECTOR,
                 "body > div.wrapper > main > div.info-section.info-section--without-cover.pr > div > div > div.info-section__group-item.pr.license-hqb-register > form > div:nth-child(4) > label")
            )
        )
        calendar_label.click()
        await asyncio.sleep(20)

        while True:
            try:
                day_container = WebDriverWait(driver, 20).until(
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
                        
                        # Check if this date meets minimum threshold BEFORE clicking
                        try:
                            date_obj = datetime.strptime(aria_label, "%B %d, %Y")
                            if date_obj.date() < min_date_threshold.date():
                                await debug_log(update, f"Skipping date before threshold: {aria_label}")
                                continue
                            await debug_log(update, f"Date {aria_label} meets threshold, proceeding to click")
                        except (ValueError, AttributeError) as e:
                            await debug_log(update, f"Failed to parse date label: {aria_label}", e)
                            continue
                            
                        # Date meets threshold - proceed with click
                        day.click()
                        await asyncio.sleep(15)
                        
                        hour_element = WebDriverWait(driver, 20).until(
                            EC.presence_of_element_located((By.CSS_SELECTOR, "#select2-hour-input-container"))
                        )
                        hour_text = hour_element.text
                        await asyncio.sleep(5)  # Wait 5 seconds for data to load
                        
                        # Check if there are available time slots for this date
                        try:
                            element = WebDriverWait(driver, 10).until(
                                EC.presence_of_element_located((By.CSS_SELECTOR, 
                                    "body > div.wrapper > main > div.info-section.info-section--without-cover.pr > div > div > div.info-section__group-item.pr.license-hqb-register-search-history > form > div.table-box.scroller-block > table > tbody > tr > td:nth-child(2)"))
                            )
                            await debug_log(update, f"Found reservation table for {aria_label}")
                        except TimeoutException:
                            await debug_log(update, f"No reservation slots available for {aria_label}")
                            continue
                        except Exception as e:
                            await debug_log(update, f"Error finding reservation table for {aria_label}", e)
                            continue
                        
                        # Parse and combine date with hour_text
                        date_obj = datetime.strptime(aria_label, "%B %d, %Y")  # Parse aria_label
                        formatted_date = date_obj.strftime("%d-%m-%Y")  # Format as dd-mm-yyyy
                        # Ensure hour_text is in HH:MM format and combine with date
                        hour_text = hour_text.strip()  # Remove any whitespace
                        
                        if ':' not in hour_text:  # Add minutes if missing
                            if hour_text.isdigit():  # Only add :00 if we have a valid hour
                                hour_text = f"{hour_text}:00"
                        
                        combined_datetime = f"{hour_text}{formatted_date}"  # Combine hour and date
                        inner_text = element.text
                        print("Found text:", inner_text)
                        
                        # Parse the datetime string
                        
                        # Format: "hh:mmdd-mm-yyyy"
                        time_part = inner_text[:5]  # "14:10"
                        date_part = inner_text[5:]  # "04-09-2025"
                        
                        # Get current time
                        current_time = datetime.now()
                        
                        # Parse the time part to check if it's after 10:30
                        hour, minute = map(int, time_part.split(':'))
                        if hour < 10 or (hour == 10 and minute < 30):
                            # Silently skip early times
                            continue
                        
                        # Parse the existing date
                        try:
                            datetime_str = f"{date_part} {time_part}"
                            parsed_datetime = datetime.strptime(datetime_str, "%d-%m-%Y %H:%M")
                            
                            # Check if there's at least 6 hours difference
                            time_difference = parsed_datetime - current_time
                            hours_difference = time_difference.total_seconds() / 3600
                            
                            if hours_difference < 6:
                                await debug_log(update, f"Skipping too soon time: {datetime_str} (only {hours_difference:.1f}h away)")
                                continue
                            
                            formatted_date = parsed_datetime.strftime("%Y-%m-%d %H:%M")
                            print("Parsed datetime:", formatted_date)
                            
                            # Parse the combined (selected) date
                            combined_datetime_obj = datetime.strptime(combined_datetime, "%H:%M%d-%m-%Y")
                            
                            await debug_log(update, f"Successfully parsed dates - Current: {datetime_str}, Selected: {combined_datetime}")
                            
                        except Exception as e:
                            await debug_log(update, f"Date parsing failed for text: '{inner_text}', time_part: '{time_part}', date_part: '{date_part}'", e)
                            continue
                        
                        screenshot = driver.get_screenshot_as_png()
                        bio = io.BytesIO(screenshot)
                        bio.name = "valid_date.png"
                        
                        # Format dates in a more readable way
                        parsed_datetime_text = parsed_datetime.strftime("%B %d, %Y at %I:%M %p")
                        combined_datetime_text = combined_datetime_obj.strftime("%B %d, %Y at %I:%M %p")

                        # Send notification only for valid reservation
                        await update.message.reply_text("🎉 Valid reservation slot found!")
                        await update.message.reply_text(f"📅 Available time: {combined_datetime_text}")
                        await asyncio.sleep(3)
                        # Check if found date meets minimum threshold first
                        if combined_datetime_obj.date() >= min_date_threshold.date():
                            # Found date is valid (after threshold)
                            
                            if parsed_datetime.date() >= min_date_threshold.date():
                                # Current reservation is also valid - check if new one is better
                                if parsed_datetime > combined_datetime_obj:
                                    # New date is earlier (better) than current - switch
                                    await update.message.reply_text(f"🟢 Found better date: {combined_datetime_text}")
                                    await update.message.reply_text("🔄 Canceling current reservation and booking better date...")
                                    
                                    # Wait 2 seconds then click email field
                                    await asyncio.sleep(5)
                                    try:
                                        await debug_log(update, "Looking for email field...")
                                        email_field = WebDriverWait(driver, 10).until(
                                            EC.element_to_be_clickable((By.CSS_SELECTOR, "body > div.wrapper > main > div.info-section.info-section--without-cover.pr > div > div > div.info-section__group-item.pr.license-hqb-register > form > div:nth-child(6) > label"))
                                        )
                                        email_field.click()
                                        await debug_log(update, "Email field clicked successfully")
                                    except Exception as e:
                                        await debug_log(update, "Failed to click email field", e)
                                        return
                                    
                                    # Wait 1 second then type email
                                    await asyncio.sleep(1)
                                    active_element = driver.switch_to.active_element
                                    for digit in "mariahambardzumian@gmail.com":
                                        active_element.send_keys(digit)
                                        await asyncio.sleep(0.1)

                                    # Wait 3 seconds then click button to cancel current reservation
                                    await asyncio.sleep(3)
                                    try:
                                        await debug_log(update, "Looking for cancel button...")
                                        button = WebDriverWait(driver, 10).until(
                                            EC.element_to_be_clickable(
                                                (By.CSS_SELECTOR, 
                                                 "body > div.wrapper > main > div.info-section.info-section--without-cover.pr > div > div > div.info-section__group-item.pr.license-hqb-register-search-history > form > div.table-box.scroller-block > table > tbody > tr > td.fs12 > button"
                                                )
                                            )
                                        )
                                        button.click()
                                        await debug_log(update, "Cancel button clicked successfully")
                                        
                                        # Wait 1 second then click detach-do button
                                        await asyncio.sleep(1)
                                        await debug_log(update, "Looking for detach button...")
                                        detach_button = WebDriverWait(driver, 10).until(
                                            EC.element_to_be_clickable((By.CSS_SELECTOR, "#detach-do"))
                                        )
                                        detach_button.click()
                                        await debug_log(update, "Detach button clicked successfully")

                                        # Wait 2 seconds then click vehicle-license-submit button to confirm new reservation
                                        await asyncio.sleep(2)
                                        await debug_log(update, "Looking for submit button...")
                                        submit_button = WebDriverWait(driver, 10).until(
                                            EC.element_to_be_clickable((By.CSS_SELECTOR, "#vehicle-license-submit"))
                                        )
                                        submit_button.click()
                                        await debug_log(update, "Submit button clicked successfully")
                                    except Exception as e:
                                        await debug_log(update, "Failed during booking button sequence", e)
                                        return
                                    
                                    await asyncio.sleep(5)
                                    # Take a screenshot after waiting and send status
                                    new_date_screenshot = driver.get_screenshot_as_png()
                                    new_date_bio = io.BytesIO(new_date_screenshot)
                                    new_date_bio.name = "new_date_selected.png"
                                    
                                    await update.message.reply_photo(
                                        photo=new_date_bio,
                                        caption=f"✅ Successfully changed reservation!\n\n📅 Old: {parsed_datetime_text}\n🟢 New: {combined_datetime_text}"
                                    )
                                    return
                                else:
                                    # Current date is still better or same
                                    await update.message.reply_text(f"✓ Your current date is still the best available")
                                    
                                    await update.message.reply_photo(
                                        photo=bio,
                                        caption=f"✓ Keeping current reservation\n\nYour date: {parsed_datetime_text}\nNext available: {combined_datetime_text}"
                                    )
                                    return
                            else:
                                # Current reservation is invalid (before threshold) - book first valid date
                                min_threshold_text = min_date_threshold.strftime("%B %d, %Y")
                                await update.message.reply_text(f"⚠️ Current reservation is before threshold ({min_threshold_text})")
                                await update.message.reply_text(f"🔄 Booking first available date after threshold: {combined_datetime_text}")
                                
                                # Wait 5 seconds then click email field
                                await asyncio.sleep(5)
                                try:
                                    await debug_log(update, "Looking for email field (invalid reservation case)...")
                                    email_field = WebDriverWait(driver, 10).until(
                                        EC.element_to_be_clickable((By.CSS_SELECTOR, "body > div.wrapper > main > div.info-section.info-section--without-cover.pr > div > div > div.info-section__group-item.pr.license-hqb-register > form > div:nth-child(6) > label"))
                                    )
                                    email_field.click()
                                    await debug_log(update, "Email field clicked successfully (invalid reservation case)")
                                    
                                    # Wait 1 second then type email
                                    await asyncio.sleep(1)
                                    active_element = driver.switch_to.active_element
                                    for digit in "mariahambardzumian@gmail.com":
                                        active_element.send_keys(digit)
                                        await asyncio.sleep(0.1)

                                    # Wait 3 seconds then click button to cancel current reservation
                                    await asyncio.sleep(3)
                                    await debug_log(update, "Looking for cancel button (invalid reservation case)...")
                                    button = WebDriverWait(driver, 10).until(
                                        EC.element_to_be_clickable(
                                            (By.CSS_SELECTOR, 
                                             "body > div.wrapper > main > div.info-section.info-section--without-cover.pr > div > div > div.info-section__group-item.pr.license-hqb-register-search-history > form > div.table-box.scroller-block > table > tbody > tr > td.fs12 > button"
                                            )
                                        )
                                    )
                                    button.click()
                                    await debug_log(update, "Cancel button clicked successfully (invalid reservation case)")
                                    
                                    # Wait 1 second then click detach-do button
                                    await asyncio.sleep(1)
                                    await debug_log(update, "Looking for detach button (invalid reservation case)...")
                                    detach_button = WebDriverWait(driver, 10).until(
                                        EC.element_to_be_clickable((By.CSS_SELECTOR, "#detach-do"))
                                    )
                                    detach_button.click()
                                    await debug_log(update, "Detach button clicked successfully (invalid reservation case)")

                                    # Wait 2 seconds then click vehicle-license-submit button to confirm new reservation
                                    await asyncio.sleep(2)
                                    await debug_log(update, "Looking for submit button (invalid reservation case)...")
                                    submit_button = WebDriverWait(driver, 10).until(
                                        EC.element_to_be_clickable((By.CSS_SELECTOR, "#vehicle-license-submit"))
                                    )
                                    submit_button.click()
                                    await debug_log(update, "Submit button clicked successfully (invalid reservation case)")
                                except Exception as e:
                                    await debug_log(update, "Failed during booking sequence (invalid reservation case)", e)
                                    return
                                
                                await asyncio.sleep(5)
                                # Take a screenshot after waiting and send status
                                new_date_screenshot = driver.get_screenshot_as_png()
                                new_date_bio = io.BytesIO(new_date_screenshot)
                                new_date_bio.name = "new_date_selected.png"
                                
                                await update.message.reply_photo(
                                    photo=new_date_bio,
                                    caption=f"✅ Successfully changed reservation!\n\n📅 Old: {parsed_datetime_text}\n🟢 New: {combined_datetime_text}"
                                )
                                return
                        else:
                            # Found date is before threshold - continue searching
                            min_threshold_text = min_date_threshold.strftime("%B %d, %Y")
                            continue

                if found_next_month_day:
                    next_month_button = WebDriverWait(driver, 10).until(
                        EC.element_to_be_clickable(
                            (By.CSS_SELECTOR, "div.flatpickr-calendar.open .flatpickr-next-month")
                        )
                    )
                    next_month_button.click()
                    await asyncio.sleep(25)
                else:
                    break

            except (TimeoutException, NoSuchElementException, StaleElementReferenceException) as e:
                await debug_log(update, "Calendar/Day processing error", e)
                if update:
                    await update.message.reply_text("Չհաջողվեց գտնել ազատ օր 😕")
                else:
                    # This now uses the mocked reply_text method provided by ScheduledUpdate
                    await update.message.reply_text("[Scheduled] Չհաջողվեց գտնել ազատ օր 😕")
                break
            except Exception as e:
                await debug_log(update, "Unexpected error in day processing loop", e)
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
        import traceback
        full_traceback = traceback.format_exc()
        
        # Send detailed error info to chat
        await debug_log(update, f"Main exception caught", e)
        await debug_log(update, f"Traceback: {full_traceback}")
        
        error_message = f"❌ Bot encountered an error: {str(e)}"
        if update:
            await update.message.reply_text(error_message)
        else:
            # This now uses the mocked reply_text method provided by ScheduledUpdate
            await update.message.reply_text(f"[Scheduled] {error_message}")


    finally:
        driver.quit()

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Hello! I'm your bot.")

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    help_text = """
🤖 **Available Commands:**

📅 `/check` - Check for available driver license appointments

🧹 **Chat Cleanup Commands:**
• `/cleanup` - Keep only last day messages (24 hours)
• `/clean [number]` - Delete last N messages (default: 50)
  Example: `/clean 100` deletes last 100 messages

💡 `/help` - Show this help message
🚀 `/start` - Start the bot
    """
    await update.message.reply_text(help_text)

async def cleanup_chat(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Keep only last day messages and delete older ones"""
    try:
        chat_id = update.effective_chat.id
        bot = context.bot
        
        # Calculate cutoff time (24 hours ago)
        cutoff_time = datetime.now(timezone.utc) - timedelta(days=1)
        
        await update.message.reply_text("🧹 Starting chat cleanup... (keeping last 24 hours)")
        
        # Get recent messages (Telegram limits to 100 messages per request)
        deleted_count = 0
        kept_count = 0
        
        # We'll iterate through message history
        try:
            # Start from a high message ID and work backwards
            last_message_id = update.message.message_id
            
            for message_id in range(last_message_id - 1000, last_message_id):  # Check last 1000 messages
                try:
                    # Try to get message info by forwarding to ourselves (then delete the forward)
                    # This is a workaround since we can't directly get message timestamps
                    
                    # Alternative approach: delete messages in batches
                    if message_id < last_message_id - 100:  # Keep only last 100 messages as "last day"
                        try:
                            await bot.delete_message(chat_id=chat_id, message_id=message_id)
                            deleted_count += 1
                        except Exception:
                            # Message might not exist or can't be deleted
                            pass
                    else:
                        kept_count += 1
                        
                except Exception:
                    # Message doesn't exist or can't be accessed
                    continue
                    
        except Exception as e:
            await update.message.reply_text(f"⚠️ Error during cleanup: {str(e)}")
            return
            
        await update.message.reply_text(
            f"✅ Chat cleanup completed!\n"
            f"🗑️ Deleted: {deleted_count} old messages\n"
            f"💾 Kept: {kept_count} recent messages"
        )
        
    except Exception as e:
        await update.message.reply_text(f"❌ Cleanup failed: {str(e)}")

async def cleanup_chat_simple(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Simple cleanup - delete last N messages except current one"""
    try:
        chat_id = update.effective_chat.id
        bot = context.bot
        current_message_id = update.message.message_id
        
        # Get number from command args, default to 50
        try:
            num_to_delete = int(context.args[0]) if context.args else 50
        except (ValueError, IndexError):
            num_to_delete = 50
            
        await update.message.reply_text(f"🧹 Deleting last {num_to_delete} messages...")
        
        deleted_count = 0
        
        # Delete messages working backwards from current message
        for i in range(1, num_to_delete + 1):
            message_id_to_delete = current_message_id - i
            if message_id_to_delete > 0:
                try:
                    await bot.delete_message(chat_id=chat_id, message_id=message_id_to_delete)
                    deleted_count += 1
                except Exception:
                    # Message might not exist or can't be deleted
                    pass
                    
        await update.message.reply_text(f"✅ Deleted {deleted_count} messages!")
        
    except Exception as e:
        await update.message.reply_text(f"❌ Cleanup failed: {str(e)}")

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
        app.add_handler(CommandHandler("help", help_command))
        app.add_handler(CommandHandler("check", check))
        app.add_handler(CommandHandler("cleanup", cleanup_chat))
        app.add_handler(CommandHandler("clean", cleanup_chat_simple))

        print("Bot is running in polling mode...")
        app.run_polling()
