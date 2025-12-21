import pytest
from playwright.async_api import async_playwright

@pytest.mark.asyncio
async def test_valid_form_submission(async_playwright):
    """Test successful form submission with valid data."""
    
    # Launch browser
    browser = await async_playwright().start()
    context = await browser.new_context()
    page = await context.new_page()
    
    # Navigate to the page
    await page.goto("https://automationexercise.com/")
    
    # Wait for the form to be loaded
    await page.wait_for_selector('[data-testid="form-container"]')
    
    # Step 1: Fill csrfmiddlewaretoken with valid data
    csrf_token_input = await page.query_selector('[name="csrf_token"]')
    if csrf_token_input:
        await csrf_token_input.fill("test_csrf_token")
    else:
        print("Failed to locate csrf token input")
        await page.screenshot(path="error_csrf_token_input.png")
        raise Exception("Failed to locate csrf token input")
    
    # Step 2: Fill with valid data
    email_input = await page.query_selector('[name="email"]')
    if email_input:
        await email_input.fill("test_email")
    else:
        print("Failed to locate email input")
        await page.screenshot(path="error_email_input.png")
        raise Exception("Failed to locate email input")
    
    # Step 3: Click submit button
    submit_button = await page.query_selector('[data-testid="submit-button"]')
    if submit_button:
        await submit_button.click()
    else:
        print("Failed to locate submit button")
        await page.screenshot(path="error_submit_button.png")
        raise Exception("Failed to locate submit button")
    
    # Step 4: Wait for response
    await page.wait_for_selector("[data-testid='success-message']")
    
    # Assert form submits successfully
    success_message = await page.query_selector('[data-testid="success-message"]')
    assert success_message, "Success message not found"
    
    # Assert success message displayed
    success_message_text = await page.query_selector('[data-testid="success-message"]').text_content()
    assert "The form has been successfully submitted" in success_message_text, "Invalid success message"
    
    # Take a screenshot
    await page.screenshot(path="success_form_submission.png")
    
    # Close browser
    await browser.close()