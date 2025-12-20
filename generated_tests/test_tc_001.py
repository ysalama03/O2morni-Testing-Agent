import pytest
from playwright.async_api import async_playwright

def test_valid_form_submission(async_playwright):
    # Initialize the browser and context
    browser = yield async_playwright().start()
    context = yield browser.new_context()
    page = yield context.new_page()

    # Visit the application URL
    yield page.goto("https://automaonexercise.com/")

    # Wait for the form to be fully loaded and visible
    yield page.wait_for_selector("#login-form")

    # Step 1: Fill csrfmiddlewaretoken with valid data
    yield page.fill('[name="csrf_token"]', "token_value")  # Replace with actual token value

    # Step 2: Fill  with valid data
    yield page.fill('[name="email"]', "hamada@example.com")
    yield page.fill('[name="password"]', "password")

    # Take a screenshot before submitting the form
    yield page.screenshot(path="form_before_submission.png")

    # Step 3: Click submit button
    submit_button = yield page.query_selector('[name="Submit"]')
    yield submit_button.click()

    # Step 4: Wait for response
    # Wait for the success message or redirect
    try:
        # Try to wait for the success message
        yield page.wait_for_selector("#success")

        # Verify that the success message is displayed
        success_message = yield page.query_selector("#success")
        assert success_message.is_visible()
        yield page.screenshot(path="success_message.png")

    except Exception as e:
        # If the success message is not found, try to wait for the redirect
        print(f"Exception caught: {e}")
        try:
            # Wait for the redirect
            yield page.wait_for_navigation()

            # Verify that the user is redirected to the expected page
            assert page.url == "https://automationexercise.com/success"

            # Take a screenshot after the redirect
            yield page.screenshot(path="redirected_page.png")

        except Exception as e:
            # If the redirect is not found, fail the test
            print(f"Exception caught during redirect: {e}")
            assert False

    finally:
        # Close the browser resources
        yield browser.close()