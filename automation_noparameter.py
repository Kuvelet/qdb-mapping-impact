# Portfolio archive: original project script; private PIM URL redacted.
# Preserves historical execution behavior, including module-level work.
# See README.md before considering any execution against a live system.

import time
import csv
import pandas as pd

from datetime import datetime
from tqdm import tqdm

from selenium import webdriver
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC


excel_file_path = "data.xlsx"
website_url = "https://example.invalid/pim/login"
log_file_path = "automation_log.txt"

# Creates a new mapping report file for each batch/run.
# Example: mapping_report_2026-05-05_14-32-10.csv
batch_start_datetime = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
report_file_path = f"mapping_report_{batch_start_datetime}.csv"


# Change this to control where the script starts.
# Example:
# 820 means start from Excel row 820.
start_excel_row = 2


def log(message):
    """
    Prints a message with a timestamp and also saves it to automation_log.txt.
    """
    current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    full_message = f"[{current_time}] {message}"

    print(full_message)

    with open(log_file_path, "a", encoding="utf-8") as log_file:
        log_file.write(full_message + "\n")


def write_report_row(
    excel_row_number,
    note_value,
    qdb_text_value,
    note_parameters_value,
    status,
    reason,
):
    """
    Writes one row result to the batch mapping report immediately.

    Status examples:
    Success
    Skipped
    Error
    """
    current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    with open(report_file_path, "a", newline="", encoding="utf-8") as report_file:
        writer = csv.writer(report_file)

        writer.writerow(
            [
                excel_row_number,
                note_value,
                qdb_text_value,
                note_parameters_value,
                status,
                reason,
                current_time,
            ]
        )


def format_elapsed_time(seconds):
    """
    Converts seconds into HH:MM:SS format.
    Example:
    3661 seconds -> 01:01:01
    """
    seconds = int(seconds)
    hours = seconds // 3600
    minutes = (seconds % 3600) // 60
    seconds = seconds % 60

    return f"{hours:02d}:{minutes:02d}:{seconds:02d}"


def xpath_literal(text):
    """
    Makes text safe to use inside XPath.
    This helps if the Excel value contains quotes.
    """
    text = str(text)

    if "'" not in text:
        return f"'{text}'"

    if '"' not in text:
        return f'"{text}"'

    parts = text.split("'")

    return "concat(" + ', "\'", '.join(f"'{part}'" for part in parts) + ")"


def format_note_parameters(value):
    """
    Keeps Note Parameters close to the Excel display style.

    If pandas reads it as a date, format it like:
    2/29/1996

    If pandas reads it as text, keep it as text.
    """
    if hasattr(value, "strftime"):
        return f"{value.month}/{value.day}/{value.year}"

    return str(value)


def open_syncfusion_dropdown(driver, element):
    """
    Opens Syncfusion dropdowns using their JavaScript instance.
    This worked better than normal Selenium click for this page.
    """
    driver.execute_script(
        """
        const dropdown = arguments[0];

        if (dropdown.ej2_instances && dropdown.ej2_instances.length > 0) {
            dropdown.ej2_instances[0].showPopup();
        } else {
            dropdown.click();
        }
        """,
        element
    )


def wait_for_spinner_to_disappear(driver, timeout=60):
    """
    Waits until the page loading spinner disappears.

    If the site gets stuck, this waits up to 60 seconds,
    then fails safely instead of clicking through the spinner.
    """
    WebDriverWait(driver, timeout).until(
        EC.invisibility_of_element_located(
            (By.CSS_SELECTOR, ".e-spinner-pane.e-spin-show")
        )
    )

    time.sleep(0.5)


def safe_click(driver, wait, locator, description):
    """
    Safer click:
    1. Waits for spinner to disappear.
    2. Waits for element to be clickable.
    3. Scrolls element into view.
    4. Clicks the element.
    """
    wait_for_spinner_to_disappear(driver)

    element = wait.until(
        EC.element_to_be_clickable(locator)
    )

    driver.execute_script(
        "arguments[0].scrollIntoView({block: 'center'});",
        element
    )

    time.sleep(0.3)

    element.click()

    log(description)

    return element


def click_text_filters_equal(driver, wait, actions):
    """
    Opens Text Filters and clicks Equal...

    This uses the original Text Filters locator that worked reliably:
    //*[contains(text(), 'Text Filters')]

    The retry is only added to protect against occasional stale menu elements.
    """
    equal_clicked = False

    for attempt in range(1, 4):
        try:
            text_filters = wait.until(
                EC.visibility_of_element_located(
                    (By.XPATH, "//*[contains(text(), 'Text Filters')]")
                )
            )

            actions.move_to_element(text_filters).perform()
            log(f"Hovered over Text Filters. Attempt {attempt}.")

            time.sleep(0.5)

            equal_option = wait.until(
                EC.element_to_be_clickable(
                    (By.XPATH, "//li[normalize-space(text())='Equal...']")
                )
            )

            equal_option.click()
            log("Clicked Equal...")

            equal_clicked = True
            break

        except Exception as error:
            log(f"Text Filters / Equal click attempt {attempt} failed.")
            log(f"Reason: {type(error).__name__}")
            time.sleep(1)

    if not equal_clicked:
        raise Exception("Could not click Text Filters > Equal... after 3 attempts.")


def select_qdb_text_from_dropdown(driver, wait, qdb_text_value):
    """
    Opens the QDB value dropdown, searches for the exact QDB Text,
    and clicks the exact matching option.

    This retry protects the fragile area where Syncfusion sometimes opens
    the dropdown search box but does not immediately refresh the matching
    list item.
    """
    qdb_selected = False
    qdb_xpath_value = xpath_literal(qdb_text_value)

    for attempt in range(1, 4):
        try:
            wait_for_spinner_to_disappear(driver)

            # Re-find the dropdown fresh on every attempt.
            dropdown_input = wait.until(
                EC.presence_of_element_located(
                    (By.ID, "DropDownListACESTagQdbParameterValues")
                )
            )

            open_syncfusion_dropdown(driver, dropdown_input)

            log(f"Opened QDB dropdown. Attempt {attempt}.")

            time.sleep(1)

            # Re-find the dropdown search input fresh on every attempt.
            dropdown_search_input = wait.until(
                EC.element_to_be_clickable(
                    (
                        By.XPATH,
                        "//div[contains(@class, 'e-popup-open')]"
                        "//input[contains(@class, 'e-input-filter')]"
                    )
                )
            )

            dropdown_search_input.clear()
            dropdown_search_input.send_keys(qdb_text_value)

            log(
                f"Typed QDB Text into the opened dropdown search bar. "
                f"Attempt {attempt}."
            )

            time.sleep(2)

            # Click exact QDB Text option.
            # The popup-open prefix makes sure we only click the currently
            # open dropdown list item, not an old hidden list item.
            qdb_dropdown_option = wait.until(
                EC.element_to_be_clickable(
                    (
                        By.XPATH,
                        f"//div[contains(@class, 'e-popup-open')]"
                        f"//li[contains(@class, 'e-list-item') "
                        f"and normalize-space(.)={qdb_xpath_value}]"
                    )
                )
            )

            driver.execute_script(
                "arguments[0].scrollIntoView({block: 'center'});",
                qdb_dropdown_option
            )

            time.sleep(0.3)

            qdb_dropdown_option.click()

            log(
                f"Clicked exact QDB Text option from dropdown. "
                f"Attempt {attempt}."
            )

            qdb_selected = True
            break

        except Exception as error:
            log(f"QDB dropdown selection attempt {attempt} failed.")
            log(f"Reason: {type(error).__name__}")
            log(str(error))

            # Close any half-open dropdown before retrying.
            try:
                ActionChains(driver).send_keys(Keys.ESCAPE).perform()
                time.sleep(1)
            except Exception:
                pass

            time.sleep(2)

    if not qdb_selected:
        raise Exception(
            "Could not select exact QDB Text from dropdown after 3 attempts."
        )


# Clear old terminal-style log at the beginning of each run.
with open(log_file_path, "w", encoding="utf-8") as log_file:
    log_file.write("")


# Create a new mapping report file for this batch.
with open(report_file_path, "w", newline="", encoding="utf-8") as report_file:
    writer = csv.writer(report_file)

    writer.writerow(
        [
            "Excel Row",
            "Note",
            "QDB Text",
            "Note Parameters",
            "Status",
            "Reason",
            "Timestamp",
        ]
    )


# Start total script timer
script_start_time = time.time()


# Read Excel file
df = pd.read_excel(excel_file_path)

log("Excel file loaded successfully.")
log(f"Total rows found: {len(df)}")
log(f"Mapping report file created: {report_file_path}")


# Start from selected Excel row.
# Excel row 1 is the header.
# Excel row 2 equals pandas index 0.
rows_to_process = df.iloc[start_excel_row - 2:]

log(f"Starting from Excel row {start_excel_row}.")
log(f"Rows remaining to process: {len(rows_to_process)}")


# Open Chrome one time.
driver = webdriver.Chrome()
driver.get(website_url)

log("Website opened successfully.")
log("Log in and go to the page where you can see the Name column filter icon.")

input("When you can see the funnel icon, press Enter here...")


# Main wait.
wait = WebDriverWait(driver, 30)
actions = ActionChains(driver)


for index, row in tqdm(
    rows_to_process.iterrows(),
    total=len(rows_to_process),
    desc="Processing Excel rows",
    unit="row"
):
    excel_row_number = index + 2

    log("====================================")
    log(f"Processing Excel row {excel_row_number}")
    log("====================================")

    note_value = row["Note"]
    qdb_text_value = row["QDB Text"]

    # Note Parameters is no longer required for this version.
    # Keep it only for the report if the column still exists in Excel.
    note_parameters_value = row.get("Note Parameters", "")

    if pd.isna(note_value):
        reason = "Note is missing"
        log(f"Skipped row {excel_row_number} - {reason}.")

        write_report_row(
            excel_row_number,
            "",
            qdb_text_value,
            note_parameters_value,
            "Skipped",
            reason,
        )

        continue

    if pd.isna(qdb_text_value):
        reason = "QDB Text is missing"
        log(f"Skipped row {excel_row_number} - {reason}.")

        write_report_row(
            excel_row_number,
            note_value,
            "",
            note_parameters_value,
            "Skipped",
            reason,
        )

        continue

    note_value = str(note_value)
    qdb_text_value = str(qdb_text_value)

    if pd.isna(note_parameters_value):
        clean_note_parameters_value = ""
    else:
        clean_note_parameters_value = format_note_parameters(note_parameters_value)

    log(f"Note: {note_value}")
    log(f"QDB Text: {qdb_text_value}")
    log("Note Parameters step is skipped in this version.")

    try:
        wait_for_spinner_to_disappear(driver)

        # Find and click the Name column filter icon.
        filter_icons = wait.until(
            EC.presence_of_all_elements_located(
                (By.CSS_SELECTOR, ".e-filtermenudiv.e-icons.e-icon-filter")
            )
        )

        log(f"Number of actual filter icons found: {len(filter_icons)}")

        filter_icons[0].click()
        log("Clicked the Name column filter icon.")

        # Hover over Text Filters and click Equal...
        click_text_filters_equal(driver, wait, actions)

        # Type the Note value into the Equal filter input.
        first_input = wait.until(
            EC.presence_of_element_located((By.ID, "Text-xlfl-frstvalue"))
        )

        first_input.clear()
        first_input.send_keys(note_value)

        log("Typed Note value into the Equal filter input.")

        # Click OK on the filter popup.
        ok_button = wait.until(
            EC.element_to_be_clickable((By.CLASS_NAME, "e-xlfl-okbtn"))
        )

        ok_button.click()
        log("Clicked OK.")

        wait_for_spinner_to_disappear(driver)

        # Wait for the filtered result to appear.
        note_xpath_value = xpath_literal(note_value)

        try:
            result_cell = wait.until(
                EC.visibility_of_element_located(
                    (
                        By.XPATH,
                        f"//*[normalize-space(text())={note_xpath_value}]"
                    )
                )
            )
        except TimeoutException:
            reason = "No filtered result found"

            log(f"{reason} for Excel row {excel_row_number}: {note_value}")
            log("Skipping this row and continuing.")

            write_report_row(
                excel_row_number,
                note_value,
                qdb_text_value,
                clean_note_parameters_value,
                "Skipped",
                reason,
            )

            continue

        # Right-click the filtered result.
        actions.context_click(result_cell).perform()
        log("Right-clicked the filtered result.")

        # Click Remove Mapping.
        remove_mapping_option = wait.until(
            EC.element_to_be_clickable(
                (By.XPATH, "//*[normalize-space(text())='Remove Mapping']")
            )
        )

        remove_mapping_option.click()
        log("Clicked Remove Mapping.")

        wait_for_spinner_to_disappear(driver)

        time.sleep(1)

        # Re-find the same result fresh after refresh.
        try:
            fresh_result_cell = wait.until(
                EC.visibility_of_element_located(
                    (
                        By.XPATH,
                        f"//*[normalize-space(text())={note_xpath_value}]"
                    )
                )
            )
        except TimeoutException:
            reason = "Filtered result disappeared after Remove Mapping"

            log(
                f"{reason} for Excel row {excel_row_number}: {note_value}"
            )
            log("Skipping this row and continuing.")

            write_report_row(
                excel_row_number,
                note_value,
                qdb_text_value,
                clean_note_parameters_value,
                "Skipped",
                reason,
            )

            continue

        driver.execute_script(
            "arguments[0].scrollIntoView({block: 'center'});",
            fresh_result_cell
        )

        fresh_result_cell.click()
        log("Left-clicked the filtered result again.")

        wait_for_spinner_to_disappear(driver)

        # Click Add QDB.
        safe_click(
            driver,
            wait,
            (By.XPATH, "//*[normalize-space(text())='Add QDB']"),
            "Clicked Add QDB."
        )

        # Wait for Add QDB popup search field.
        qdb_search_input = wait.until(
            EC.element_to_be_clickable((By.ID, "TextBoxACESTagQdbSearch"))
        )

        qdb_search_input.clear()
        qdb_search_input.send_keys(qdb_text_value)

        log("Typed QDB Text into Add QDB search field.")

        # Press Enter to search.
        qdb_search_input.send_keys(Keys.ENTER)
        log("Pressed Enter in the QDB search field.")

        wait_for_spinner_to_disappear(driver)

        time.sleep(2)

        # Select exact QDB Text from the QDB dropdown.
        # This section now has its own retry logic.
        select_qdb_text_from_dropdown(driver, wait, qdb_text_value)

        wait_for_spinner_to_disappear(driver)

        time.sleep(1)

        # No Parameter dropdown / Value field / Add Parameter step needed.
        # After selecting the QDB value, save the Add QDB dialog directly.
        log("Skipped Parameter dropdown, Value field, and Add Parameter step.")

        # Click Save button.
        safe_click(
            driver,
            wait,
            (
                By.XPATH,
                "//div[@id='ACESTagAddQDBDialog']"
                "//button[normalize-space(text())='Save']"
            ),
            "Clicked Save button."
        )

        wait_for_spinner_to_disappear(driver)

        log(f"Finished Excel row {excel_row_number}")

        write_report_row(
            excel_row_number,
            note_value,
            qdb_text_value,
            clean_note_parameters_value,
            "Success",
            "Mapped successfully",
        )

        elapsed_so_far = time.time() - script_start_time
        log(f"Runtime so far: {format_elapsed_time(elapsed_so_far)}")

        time.sleep(2)

    except Exception as error:
        error_type = type(error).__name__
        error_message = str(error)

        log(f"Something went wrong on Excel row {excel_row_number}")
        log(f"Note: {note_value}")
        log(f"QDB Text: {qdb_text_value}")
        log(f"Note Parameters: {clean_note_parameters_value}")
        log("Error type:")
        log(error_type)
        log("Error details:")
        log(error_message)

        write_report_row(
            excel_row_number,
            note_value,
            qdb_text_value,
            clean_note_parameters_value,
            "Error",
            f"{error_type}: {error_message}",
        )

        script_error_time = time.time()
        runtime_until_error = script_error_time - script_start_time

        log(f"Runtime before error: {format_elapsed_time(runtime_until_error)}")

        input(
            "The script paused because of an unexpected error. "
            "Check the browser, then press Enter to close Chrome..."
        )

        driver.quit()
        raise


script_end_time = time.time()
total_runtime = script_end_time - script_start_time

log("Loop finished.")
log(f"Total script runtime: {format_elapsed_time(total_runtime)}")
log(f"Mapping report saved as: {report_file_path}")

input("\nLoop finished. Press Enter to close Chrome...")

driver.quit()
