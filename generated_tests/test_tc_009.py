import pytest
from playwright.async_api import async_playwright

# Test Case: form_0 Required Field Validation (view_cart)
@pytest.mark.asyncio
async def test_form_0_required_field_validation(async_playwright):
    """
    Test that required fields show validation errors when empty on https://automationexercise.com/view_cart
    """
    browser = await async_playwright().start()
    context = await browser.new_context()
    page = await context.new_page()

    # Navigate to the view_cart page
    await page.goto("https://automationexercise.com/view_cart")

    # Wait for the form to load
    await page.wait_for_selector("#product_section")

    # Leave required fields empty
    # Use data-testid attribute as the locator strategy
    await page.fill("[data-testid='first_name']", "")
    await page.fill("[data-testid='last_name']", "")
    await page.fill("[data-testid='email']", "")
    await page.fill("[data-testid='shipping_address']", "")

    # Wait for the submit button to be enabled
    await page.wait_for_selector("[data-testid='submit_button']")

    # Click submit button
    await page.click("[data-testid='submit_button']")

    # Wait for the validation errors to appear
    await page.wait_for_selector("[data-testid='error_message'].text")

    # Assert that validation errors are displayed
    error_messages = await page.query_selector_all("[data-testid='error_message']")
    assert len(error_messages) == 4  # 4 expected error messages

    # Screenshot at key verification point
    await page.screenshot(path="error_messages.png")

    # Assert that form is not submitted
    await page.wait_for_url("https://automationexercise.com/view_cart")

    # Screenshot at key verification point
    await page.screenshot(path="form_not_submitted.png")

    await browser.close()