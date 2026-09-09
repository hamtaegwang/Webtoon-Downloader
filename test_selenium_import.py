try:
    from selenium import webdriver
    print(f"Selenium imported from: {webdriver.__file__}")
    from selenium.webdriver.chrome.service import Service
    print("Service imported")
    from selenium.webdriver.chrome.options import Options
    print("Options imported")
    # This is what often causes the error if paths are weird
    from selenium.webdriver.chrome.webdriver import WebDriver
    print("WebDriver class imported")
except ImportError as e:
    print(f"ImportError: {e}")
except Exception as e:
    print(f"Error: {e}")
