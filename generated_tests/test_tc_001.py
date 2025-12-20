import pytest
from playwright.async_api import async_playwright

@pytest.mark.asyncio
async def test_valid_form_submission(async_playwright):
    """
    Test successful form submission with valid data.

    Steps:
    1. Fill csrfmiddlewaretoken with valid data
    2. Fill  with valid data
    3. Click submit button
    4. Wait for response

    Expected Results:
    - Form submits successfully
    - Success message displayed or redirect occurs
    """
    browser = await async_playwright().start()
    context = await browser.new_context()
    page = await context.new_page()

    # Step 1: Navigate to the URL
    await page.goto("https://automationexercise.com/")

    # Step 2: Wait for the form to load
    await page.wait_for_selector("#header_section")

    # Step 3: Fill in the form data
    await page.fill("[data-testid='csrfmiddlewaretoken']", "test")
    await page.fill("[name='email']", "test@example.com")
    await page.fill("[name='password']", "password")

    # Step 4: Take a screenshot before submitting
    await page.screenshot(path="screenshot_before_submit.png")

    # Step 5: Click the submit button
    await page.click("[role='button'][name='Submit']")

    # Step 6: Wait for the response
    await page.wait_for_selector("#result")

    # Step 7: Take a screenshot after submitting
    await page.screenshot(path="screenshot_after_submit.png")

    # Step 8: Verify the success message
    await page.wait_for_function("return document.querySelector('#result').innerHTML.includes('Success:')")

    # Assert that the form submitted successfully
    assert await page.query_selector("#result") is not None, "Form submission failed"

    # Assert that the success message is displayed
    success_message = await page.query_selector("body > div > div > div > div > div > div > div > div > h2")
    assert success_message is not None, "Success message not displayed"

    # Clean up
    await browser.close()