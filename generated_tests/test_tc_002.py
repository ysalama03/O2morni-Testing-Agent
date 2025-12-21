import pytest
from playwright.async_api import async_playwright

# Test Case: form_0 Required Field Validation (page)
@pytest.mark.asyncio
async def test_form_0_required_field_validation(async_playwright):
    """
    Test that required fields show validation errors when empty on https://automationexercise.com/
    """
    # Create a new browser instance
    browser = await async_playwright().start()
    context = await browser.new_context()
    page = await context.new_page()

    # Navigate to the test page
    await page.goto("https://automationexercise.com/")

    # Wait for the form to load
    await page.wait_for_selector("[data-testid='form']")

    # Leave required fields empty
    # Locator strategy: data-testid attribute
    required_fields = [
        "[data-testid='name']",  # Name
        "[data-testid='email']",  # Email
        "[data-testid='password']",  # Password
    ]

    for field in required_fields:
        # Wait for the field to be visible
        await page.wait_for_selector(field)
        # Clear the field
        await page.fill(field, "")

    # Click submit button
    # Locator strategy: Role + text
    submit_button = "role=button[name='Submit']"
    await page.wait_for_selector(submit_button)
    await page.click(submit_button)

    # Take a screenshot of the page
    await page.screenshot(path="screenshots/form_0_required_field_validation_before.png")

    # Check that validation errors are displayed
    # Locator strategy: data-testid attribute
    validation_errors = "[data-testid='validation-error-message']"
    await page.wait_for_selector(validation_errors)
    errors = await page.query_selector_all(validation_errors)
    assert len(errors) > 0, "Validation errors are not displayed"

    # Check that form is not submitted
    # Locator strategy: data-testid attribute
    form = "[data-testid='form']"
    await page.wait_for_selector(form)
    assert await page.query_selector(form) is not None, "Form is submitted"

    # Take a screenshot of the page
    await page.screenshot(path="screenshots/form_0_required_field_validation_after.png")

    # Close the browser instance
    await browser.close()