import pytest
from playwright.sync_api import sync_playwright
from playwright.async_api import async_playwright
import time

@pytest.mark.asyncio
async def test_valid_form_0_submission(async_playwright):
    """
    Test successful form submission with valid data on https://automationexercise.com/view_cart
    """
    # Launch browser
    browser = await async_playwright().start()
    context = await browser.new_context()
    page = await context.new_page()

    # Navigate to view_cart
    await page.goto("https://automationexercise.com/view_cart")

    # Step 1: Fill csrfmiddlewaretoken with valid data
    await page.wait_for_selector("#csrf_token")
    await page.fill("#csrf_token", "test_token")
    await page.screenshot(path="screenshot_1.png")

    # Step 2: Fill with valid data
    await page.wait_for_selector("#email")
    await page.fill("#email", "test_email@example.com")
    await page.screenshot(path="screenshot_2.png")

    # Step 3: Click submit button
    await page.wait_for_selector("[data-testid='single-product-add-to-cart-form']")
    await page.click("[data-testid='single-product-add-to-cart-form']")

    # Step 4: Wait for response
    await page.wait_for_selector("#cart_details")
    await page.screenshot(path="screenshot_3.png")

    # Expected Results: Form submits successfully
    assert await page.query_selector("#cart_details") is not None, "Cart details not found"

    # Expected Results: Success message displayed or redirect occurs
    assert await page.query_selector("#success_message") is not None, "Success message not found"

    # Close browser
    await browser.close()