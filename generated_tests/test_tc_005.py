# Import required libraries
import pytest
from playwright.async_api import async_playwright

# Define the test function with async pattern
async def test_valid_form_1_submission(async_playwright):
    """
    Test successful form submission with valid data on https://automationexercise.com/login
    """
    
    # Initialize the browser and context
    browser = await async_playwright().start()
    context = await browser.new_context()
    page = await context.new_page()

    # Navigate to the login page
    await page.goto("https://automationexercise.com/login")

    # Wait for the form to load
    await page.wait_for_selector("#login")

    # Fill the csrfmiddlewaretoken field with valid data
    await page.fill("[name='csrf_token']", "valid_data")

    # Fill the name field with valid data
    await page.fill("[name='name']", "John Doe")

    # Fill the email field with valid data
    await page.fill("[name='email']", "john.doe@example.com")

    # Fill the form_type field with valid data
    await page.fill("[name='form_type']", "Login")

    # Take a screenshot before submitting the form
    await page.screenshot(path="before_submit.png")

    # Click the submit button
    await page.click("[data-testid='login-form']")

    # Wait for the response to load
    await page.wait_for_selector("[data-testid='login-form-response']")

    # Take a screenshot after submitting the form
    await page.screenshot(path="after_submit.png")

    # Verify that the form submits successfully
    assert await page.query_selector("[data-testid='login-form-response']") is not None

    # Verify that the success message is displayed
    assert await page.query_selector("[data-testid='success-message']") is not None

    # Close the browser
    await browser.close()

# Run the test using pytest-playwright
pytest.main(["-v", "--junit-xml=report.xml", "test_valid_form_1_submission.py"])