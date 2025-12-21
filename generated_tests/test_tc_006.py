import pytest
from playwright.sync_api import sync_playwright
from playwright.async_api import async_playwright

# Test fixture to initialize browser
@pytest.fixture
async def browser():
    browser = await async_playwright().start()
    context = await browser.context_options().new_context()
    page = await context.new_page()
    yield page
    await browser.close()

# Test function
async def test_form_1_required_field_validation(browser: async_playwright.Page):
    """
    Test that required fields show validation errors when empty on https://automationexercise.com/login
    """
    # Specify test URL
    url = "https://automationexercise.com/login"

    # Navigate to the test URL
    await browser.goto(url)

    # Step 1: Leave required fields empty
    # Explicitly wait for the form fields
    await browser.wait_for_selector('#email')
    await browser.wait_for_selector('#password')

    # Fill in empty values
    await browser.fill('#email', '')
    await browser.fill('#password', '')

    # Step 2: Click submit button
    # Explicitly wait for the submit button
    await browser.wait_for_selector('button[type="submit"]', state='visible')
    
    # Click submit button
    await browser.click('button[type="submit"]')

    # Expected Results:
    # - Validation errors are displayed
    # Take a screenshot at this verification point
    await browser.screenshot(path='screenshots/validation_errors.png')

    # Verify validation errors are displayed
    await browser.wait_for_selector('#email+#email_error', state='visible')
    await browser.wait_for_selector('#password+#password_error', state='visible')

    # Verify form is not submitted
    # Check for homepage URL or a specific text
    await browser.wait_for_selector('#home_title', state='visible')

    # Assertions for each expected result
    assert "Invalid email or password" in await browser.get_element('#email+#email_error').text_content()
    assert "Password should have minimum 3 and maximum 50 characters" in await browser.get_element('#password+#password_error').text_content()
    assert browser.url == url