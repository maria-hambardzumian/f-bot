import io
import asyncio
import os
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.action_chains import ActionChains
from selenium.common.exceptions import TimeoutException, NoSuchElementException


async def check(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Starting Chrome...")
    await asyncio.sleep(2)
    
    # Configure Chrome options for headless environment
    chrome_options = Options()
    chrome_options.add_argument("--headless")  # Ensure GUI is not required
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--window-size=1920,1080")
    
    driver = webdriver.Chrome(options=chrome_options)
    try:
        driver.set_window_size(1728, 992)
        driver.get("https://roadpolice.am/en")
        await asyncio.sleep(2)
        # Step 1: Click the button to open the modal
        button_span = WebDriverWait(driver, 20).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR,
                "#index_page_steps > div > div > div > div:nth-child(3) > button > span > span"))
        )
        button = button_span.find_element(By.XPATH, "./ancestor::button")
        button.click()
# document.querySelector("#hqb-login-submit")
        await asyncio.sleep(0.2)  # short wait to make sure modal is fully open

        # Step 2: Send POST request in the background
        actions = ActionChains(driver)
        actions.send_keys(Keys.TAB).pause(0.4).send_keys(Keys.TAB).perform()

        await asyncio.sleep(1)  # Wait half a second before screenshot
        active_element = driver.switch_to.active_element
        
        # Get NUMBER1 from environment variable
        number1 = os.getenv('NUMBER1')
        if not number1:
            raise ValueError("NUMBER1 environment variable must be set")
        for digit in number1:
            active_element.send_keys(digit)
            await asyncio.sleep(0.1)

        actions.send_keys(Keys.TAB).perform()
        await asyncio.sleep(0.3)

        active_element = driver.switch_to.active_element
        # Get NUMBER2 from environment variable
        number2 = os.getenv('NUMBER2')
        if not number2:
            raise ValueError("NUMBER2 environment variable must be set")
        for digit in number2:
            active_element.send_keys(digit)
            await asyncio.sleep(0.1)

        actions.send_keys(Keys.TAB).perform()

        await asyncio.sleep(0.5)
        submit_button = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, "#hqb-login-submit"))
        )
        submit_button.click()


        await asyncio.sleep(1.5)
        
        # Scroll down the page
        driver.execute_script("window.scrollTo(0, 200);")

        # Step 8: Click on the dropdown (Select2-style)
        dropdown = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR,
                "body > div > main > div.info-section.info-section--without-cover.pr > div > div > div.info-section__group-item.pr.license-hqb-register > form > div:nth-child(2) > span > span.selection > span"))
        )
        dropdown.click()


        await asyncio.sleep(0.3)
        actions = ActionChains(driver)
        actions.send_keys(Keys.ARROW_DOWN).pause(0.1)
        actions.send_keys(Keys.ARROW_DOWN).pause(0.1)
        actions.send_keys(Keys.ENTER).perform()

        await asyncio.sleep(0.5)

        # Click second dropdown (location/branch)
        second_dropdown = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR,
                "body > div > main > div.info-section.info-section--without-cover.pr > div > div > div.info-section__group-item.pr.license-hqb-register > form > div:nth-child(3) > span > span.selection > span"))
        )
        second_dropdown.click()
        await asyncio.sleep(0.3)

        # Step 4: Select specific branch option
        actions = ActionChains(driver)
        actions.send_keys(Keys.ARROW_DOWN).pause(0.1)
        actions.send_keys(Keys.ARROW_DOWN).pause(0.1)
        actions.send_keys(Keys.ENTER).perform()


        await asyncio.sleep(7)
        calendar_label = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR,
                "body > div.wrapper > main > div.info-section.info-section--without-cover.pr > div > div > div.info-section__group-item.pr.license-hqb-register > form > div:nth-child(4) > label"))
        )
        calendar_label.click()
        await asyncio.sleep(10)

     
        while True:
            try:
                day_container = WebDriverWait(driver, 5).until(
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
                        await asyncio.sleep(10)
                        
                        hour_element = WebDriverWait(driver, 10).until(
                            EC.presence_of_element_located((By.CSS_SELECTOR, "#select2-hour-input-container"))
                        )
                        hour_text = hour_element.text
                        await asyncio.sleep(2)  # Wait 2 seconds
                        
                        # Combine aria_label (date) with hour_text
                        date_obj = datetime.strptime(aria_label, "%B %d, %Y")  # Parse aria_label
                        formatted_date = date_obj.strftime("%d-%m-%Y")  # Format as dd-mm-yyyy
                        combined_datetime = f"{hour_text}{formatted_date}"  # Combine hour and date
                        print("Combined datetime:", combined_datetime)

                        
                        element = WebDriverWait(driver, 10).until(
                            EC.presence_of_element_located((By.CSS_SELECTOR, 
                                "body > div.wrapper > main > div.info-section.info-section--without-cover.pr > div > div > div.info-section__group-item.pr.license-hqb-register-search-history > form > div.table-box.scroller-block > table > tbody > tr > td:nth-child(2)"))
                        )
                        inner_text = element.text
                        print("Found text:", inner_text)
                        
                        # Parse the datetime string
                        
                        # Format: "hh:mmdd-mm-yyyy"
                        time_part = inner_text[:5]  # "14:10"
                        date_part = inner_text[5:]  # "04-09-2025"
                        
                        # Parse the existing date
                        datetime_str = f"{date_part} {time_part}"
                        parsed_datetime = datetime.strptime(datetime_str, "%d-%m-%Y %H:%M")
                        formatted_date = parsed_datetime.strftime("%Y-%m-%d %H:%M")
                        print("Parsed datetime:", formatted_date)
                        
                        # Parse the combined (selected) date
                        combined_datetime_obj = datetime.strptime(combined_datetime, "%H:%M%d-%m-%Y")
                        
                        screenshot = driver.get_screenshot_as_png()
                        bio = io.BytesIO(screenshot)
                        bio.name = "valid_date.png"
                        
                        # Format dates in a more readable way
                        parsed_datetime_text = parsed_datetime.strftime("%B %d, %Y at %I:%M %p")
                        combined_datetime_text = combined_datetime_obj.strftime("%B %d, %Y at %I:%M %p")

                        # First send the submitted date
                        await update.message.reply_text(f"📅 Your submitted date: {parsed_datetime_text}")
                        
                        # Then prepare the caption for the comparison result
                        if parsed_datetime > combined_datetime_obj:
                            caption = f"🟢 New earlier date available!\n\nClosest available date:\n{combined_datetime_text}"
                        else:
                            caption = f"✓ Submitted date is the earliest\n\nClosest available date:\n{combined_datetime_text}"
                            
                        await update.message.reply_photo(
                            photo=bio,
                            caption=caption
                        )
                        return

                if found_next_month_day:
                    next_month_button = WebDriverWait(driver, 3).until(
                        EC.element_to_be_clickable(
                            (By.CSS_SELECTOR, "div.flatpickr-calendar.open .flatpickr-next-month")
                        )
                    )
                    next_month_button.click()
                    await asyncio.sleep(15)
                else:
                    break

            except (TimeoutException, NoSuchElementException):
                await update.message.reply_text("Չհաջողվեց գտնել ազատ օր 😕")
                break

        # await asyncio.sleep(5)

        # Step 3: Take screenshot
        png_bytes = driver.get_screenshot_as_png()
        bio = io.BytesIO(png_bytes)
        bio.name = "screenshot_after_post.png"

        await update.message.reply_photo(photo=bio, caption="Screenshot after background request.")

    except Exception as e:
        await update.message.reply_text(f"Error occurred: {e}")
    finally:
        driver.quit()



async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Hello! I'm your bot.")


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Here's how you can use me!")

# Main function
async def main():
    # Get token from environment variable
    token = os.getenv('TELEGRAM_TOKEN')
    chat_id = os.getenv('CHAT_ID')
    
    if not token or not chat_id:
        print("Error: TELEGRAM_TOKEN and CHAT_ID environment variables must be set")
        return
        
    app = ApplicationBuilder().token(token).build()
    
    # In GitHub Actions, we'll just run the check command directly
    if os.getenv('GITHUB_ACTIONS'):
        print("Running in GitHub Actions...")
        update = Update(0, None)
        update.message = type('obj', (object,), {
            'reply_text': lambda text: print(f"Bot would send: {text}"),
            'reply_photo': lambda photo, caption: print(f"Bot would send photo with caption: {caption}"),
            'chat_id': chat_id
        })
        await check(update, None)
    else:
        # Normal bot operation for local development
        app.add_handler(CommandHandler("start", start))
        app.add_handler(CommandHandler("help", help_command))
        app.add_handler(CommandHandler("check", check))
        print("Bot is running...")
        await app.run_polling()

if __name__ == '__main__':
    asyncio.run(main())
