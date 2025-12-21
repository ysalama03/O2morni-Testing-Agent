# Import necessary libraries
import pytest
from playwright.async_api import async_playwright

# Define a test function using pytest-playwright with async pattern
@pytest.mark.asyncio
async def test_form_0_required_field_validation(async_playwright):
    """
    Test that required fields show validation errors when empty on the login page.

    Steps:
    1. Leave required fields empty
    2. Click submit button

    Expected Results:
    - Validation errors are displayed
    - Form is not submitted
    """
    # Create a Playwright context and browser
    async with async_playwright() as p:
        browser = await p.chromium.launch()
        context = await browser.new_context()
        page = await context.new_page()

        # Set the browser viewport to a suitable size
        await page.set_viewport_size({"width": 1920, "height": 1080})

        # Navigate to the login page
        await page.goto("https://automationexercise.com/login")

        # Wait for the submit button to be clickable
        submit_button = await page.wait_for_selector("[name='submit']", state='visible')

        # Leave required fields empty
        # Email input field has data-testid attribute, but no other fields do
        # So, we'll use ID selector for email and name attributes for other fields
        email_input = await page.wait_for_selector("[name='email']", state='visible')
        password_input = await page.wait_for_selector("[name='password']", state='visible')

        # Clear input fields
        await email_input.fill("")
        await password_input.fill("")

        # Wait for the submit button to be clickable
        submit_button = await page.wait_for_selector("[name='submit']", state='visible')

        # Click the submit button
        await submit_button.click()

        # Wait for the form to be submitted (i.e., wait for validation errors to appear)
        validation_errors = await page.wait_for_selector("[data-testid='alert']", state='visible')

        # Verify that validation errors are displayed
        assert await page.query_selector("div.alert.alert-danger") is not None, "Validation errors are not displayed"

        # Verify that form is not submitted
        assert await page.query_selector("[name='email']") is not None, "Form is submitted"

        # Take a screenshot of the page
        await page.screenshot(path='screenshots/validation_errors.png')

        # Close the browser
        await browser.close()