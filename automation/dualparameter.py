"""Attended dual-parameter mapping workflow adapted from the supplied script.

Default: local workbook preview. Live runs replace existing PIM mappings.
See docs/python-automation.md for provenance, prerequisites, and limitations.
"""

import csv
import time
from datetime import datetime

from automation.runtime import (
    create_run_paths, load_workbook, parse_settings, selected_row_count, show_preview,
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


def format_parameter_value(value):
    """Format date-like values as M/D/YYYY; stringify other values."""
    if hasattr(value, "strftime"):
        return f"{value.month}/{value.day}/{value.year}"

    return str(value)


def main(argv=None):
    settings = parse_settings("dual-parameter", argv)
    df = load_workbook(settings)
    if not settings.execute:
        show_preview(settings, df)
        return 0
    if selected_row_count(len(df), settings.start_row, settings.limit) == 0:
        raise ValueError("No input rows selected; browser execution cancelled.")

    import pandas as pd
    from tqdm import tqdm
    from selenium import webdriver
    from selenium.common.exceptions import TimeoutException
    from selenium.webdriver.common.by import By
    from selenium.webdriver.common.keys import Keys
    from selenium.webdriver.common.action_chains import ActionChains
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC

    website_url = settings.url
    start_excel_row = settings.start_row
    log_file_path, report_file_path = create_run_paths(settings)

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
        note1_parameter_value,
        note2_parameter_value,
        status,
        reason,
    ):
        """
        Writes one row result to the batch mapping report immediately.

        Status examples:
        Submitted
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
                    note1_parameter_value,
                    note2_parameter_value,
                    status,
                    reason,
                    current_time,
                ]
            )





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
        then raises a timeout; earlier changes are not rolled back.
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


    def add_qdb_parameter_by_index(driver, wait, parameter_index, parameter_value, parameter_label):
        """
        Adds one QDB parameter row by selecting a parameter based on dropdown order.

        parameter_index:
            0 = first visible option
            1 = second visible option

        This function waits until the dropdown options are visible,
        logs the full option list Selenium sees, then clicks the requested index.
        """
        wait_for_spinner_to_disappear(driver)

        parameter_dropdown_input = wait.until(
            EC.presence_of_element_located(
                (By.ID, "DropDownListACESTagQdbParameter")
            )
        )

        open_syncfusion_dropdown(driver, parameter_dropdown_input)

        log(f"Opened Parameter dropdown for {parameter_label}.")

        time.sleep(0.5)

        parameter_options = wait.until(
            lambda current_driver: [
                element
                for element in current_driver.find_elements(
                    By.XPATH,
                    "//div[contains(@class, 'e-popup-open')]"
                    "//li[contains(@class, 'e-list-item')]"
                )
                if element.is_displayed()
            ]
        )

        option_texts = [element.text.strip() for element in parameter_options]
        log(f"Visible Parameter options for {parameter_label}: {option_texts}")

        if len(parameter_options) <= parameter_index:
            raise Exception(
                f"Could not find parameter option index {parameter_index} "
                f"for {parameter_label}. Visible options: {option_texts}"
            )

        parameter_option = parameter_options[parameter_index]

        driver.execute_script(
            "arguments[0].scrollIntoView({block: 'center'});",
            parameter_option
        )

        time.sleep(0.3)

        selected_option_text = parameter_option.text.strip()

        parameter_option.click()

        log(
            f"Clicked parameter option index {parameter_index} "
            f"for {parameter_label}: {selected_option_text}"
        )

        wait_for_spinner_to_disappear(driver)

        value_input = wait.until(
            EC.element_to_be_clickable((By.ID, "TextBoxACESTagQdbValue"))
        )

        log(f"Value field is ready for {parameter_label}.")

        value_input.clear()
        value_input.send_keys(parameter_value)

        log(f"Typed {parameter_label} value into the Value field: {parameter_value}")

        safe_click(
            driver,
            wait,
            (By.ID, "ButtonACESTagQdbAddParameter"),
            f"Clicked Add button for {parameter_label}."
        )

        wait_for_spinner_to_disappear(driver)

        time.sleep(1)

    # Initialize the log inside this run's new output directory.
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
                "Note1 Parameter",
                "Note2 Parameter",
                "Status",
                "Reason",
                "Timestamp",
            ]
        )


    # Start total script timer.
    script_start_time = time.time()


    # Workbook was loaded and headers checked before enabling the browser.

    log("Excel file loaded successfully.")
    log(f"Total rows found: {len(df)}")
    log(f"Mapping report file created: {report_file_path}")


    # Start from selected Excel row.
    # Excel row 1 is the header.
    # Excel row 2 equals pandas index 0.
    rows_to_process = df.iloc[start_excel_row - 2:start_excel_row - 2 + settings.limit]

    log(f"Starting from Excel row {start_excel_row}.")
    log(f"Rows remaining to process: {len(rows_to_process)}")


    # Open Chrome one time.
    driver = webdriver.Chrome()
    try:
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
            note1_parameter_value = row["Note1 Parameter"]
            note2_parameter_value = row["Note2 Parameter"]

            if pd.isna(note_value):
                reason = "Note is missing"
                log(f"Skipped row {excel_row_number} - {reason}.")

                write_report_row(
                    excel_row_number,
                    "",
                    qdb_text_value,
                    note1_parameter_value,
                    note2_parameter_value,
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
                    note1_parameter_value,
                    note2_parameter_value,
                    "Skipped",
                    reason,
                )

                continue

            if pd.isna(note1_parameter_value):
                reason = "Note1 Parameter is missing"
                log(f"Skipped row {excel_row_number} - {reason}.")

                write_report_row(
                    excel_row_number,
                    note_value,
                    qdb_text_value,
                    "",
                    note2_parameter_value,
                    "Skipped",
                    reason,
                )

                continue

            if pd.isna(note2_parameter_value):
                reason = "Note2 Parameter is missing"
                log(f"Skipped row {excel_row_number} - {reason}.")

                write_report_row(
                    excel_row_number,
                    note_value,
                    qdb_text_value,
                    note1_parameter_value,
                    "",
                    "Skipped",
                    reason,
                )

                continue

            note_value = str(note_value)
            qdb_text_value = str(qdb_text_value)
            clean_note1_parameter_value = format_parameter_value(note1_parameter_value)
            clean_note2_parameter_value = format_parameter_value(note2_parameter_value)

            log(f"Note: {note_value}")
            log(f"QDB Text: {qdb_text_value}")
            log(f"Note1 Parameter: {clean_note1_parameter_value}")
            log(f"Note2 Parameter: {clean_note2_parameter_value}")

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
                        clean_note1_parameter_value,
                        clean_note2_parameter_value,
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
                except TimeoutException as error:
                    raise RuntimeError(
                        "Filtered result disappeared after Remove Mapping. "
                        "The original mapping may already be removed; stop and inspect PIM."
                    ) from error


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

                # Open the QDB dropdown.
                dropdown_input = wait.until(
                    EC.presence_of_element_located(
                        (By.ID, "DropDownListACESTagQdbParameterValues")
                    )
                )

                open_syncfusion_dropdown(driver, dropdown_input)

                log("Opened QDB dropdown.")

                time.sleep(1)

                # Search inside opened QDB dropdown.
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

                log("Typed QDB Text into the opened dropdown search bar.")

                time.sleep(1)

                # Click exact QDB Text option.
                qdb_xpath_value = xpath_literal(qdb_text_value)

                qdb_dropdown_option = wait.until(
                    EC.element_to_be_clickable(
                        (
                            By.XPATH,
                            f"//li[contains(@class, 'e-list-item') "
                            f"and normalize-space(.)={qdb_xpath_value}]"
                        )
                    )
                )

                qdb_dropdown_option.click()

                log("Clicked exact QDB Text option from dropdown.")

                wait_for_spinner_to_disappear(driver)

                time.sleep(1)

                # Add Parameter 1 from Note1 Parameter.
                # This opens the Parameter dropdown, waits for the full visible option list,
                # then clicks index 0.
                add_qdb_parameter_by_index(
                    driver=driver,
                    wait=wait,
                    parameter_index=0,
                    parameter_value=clean_note1_parameter_value,
                    parameter_label="Note1 Parameter",
                )

                # Add Parameter 2 from Note2 Parameter.
                # This opens the Parameter dropdown again, waits for the visible option list,
                # then clicks index 1.
                add_qdb_parameter_by_index(
                    driver=driver,
                    wait=wait,
                    parameter_index=1,
                    parameter_value=clean_note2_parameter_value,
                    parameter_label="Note2 Parameter",
                )

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
                    clean_note1_parameter_value,
                    clean_note2_parameter_value,
                    "Submitted",
                    "Save clicked; persistence not independently verified",
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
                log(f"Note1 Parameter: {clean_note1_parameter_value}")
                log(f"Note2 Parameter: {clean_note2_parameter_value}")
                log("Error type:")
                log(error_type)
                log("Error details:")
                log(error_message)

                write_report_row(
                    excel_row_number,
                    note_value,
                    qdb_text_value,
                    clean_note1_parameter_value,
                    clean_note2_parameter_value,
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

                raise


        script_end_time = time.time()
        total_runtime = script_end_time - script_start_time

        log("Loop finished.")
        log(f"Total script runtime: {format_elapsed_time(total_runtime)}")
        log(f"Mapping report saved as: {report_file_path}")

        input("\nLoop finished. Press Enter to close Chrome...")
    finally:
        driver.quit()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
