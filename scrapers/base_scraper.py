from abc import ABC, abstractmethod
from typing import Optional
import pandas as pd
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager

class BaseScraper(ABC):
    """Base class for all web scrapers."""
    
    def __init__(self):
        """Initialize base scraper."""
        self.driver = None
        
    def _initialize_driver(self) -> webdriver.Chrome:
        """Initialize Chrome WebDriver with common options."""
        chrome_options = Options()
        
        # Basic configuration
        # chrome_options.add_argument("--headless")  # Enable headless mode for all scrapers
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        
        # Window configuration
        chrome_options.add_argument("--start-maximized")
        chrome_options.add_argument("--window-size=1920,1080")
        
        # Disable unwanted features
        chrome_options.add_argument("--disable-notifications")
        chrome_options.add_argument("--disable-popup-blocking")
        chrome_options.add_argument("--disable-blink-features=AutomationControlled")
        chrome_options.add_argument("--disable-extensions")
        
        # Enhanced anti-bot detection bypass
        chrome_options.add_experimental_option("excludeSwitches", [
            "enable-automation",
            "enable-logging"
        ])
        chrome_options.add_experimental_option("useAutomationExtension", False)
        
        # Random user agent that looks more like a real browser
        chrome_options.add_argument(
            "user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/120.0.0.0 Safari/537.36"
        )
        
        # Additional performance options
        chrome_options.add_argument("--disable-software-rasterizer")
        chrome_options.add_argument("--disable-web-security")
        chrome_options.add_argument("--allow-running-insecure-content")
        chrome_options.add_argument("--disable-site-isolation-trials")
        
        # Create driver with enhanced options
        driver = webdriver.Chrome(
            service=Service(ChromeDriverManager().install()),
            options=chrome_options
        )
        
        # Execute CDP commands to prevent detection
        driver.execute_cdp_cmd("Page.addScriptToEvaluateOnNewDocument", {
            "source": """
                // Overwrite the 'webdriver' property
                Object.defineProperty(navigator, 'webdriver', {
                    get: () => undefined
                });
                
                // Overwrite the 'chrome' property
                Object.defineProperty(window, 'chrome', {
                    get: () => ({
                        runtime: {},
                        // Add other chrome properties as needed
                    }),
                });
                
                // Override permissions
                const originalQuery = window.navigator.permissions.query;
                window.navigator.permissions.query = (parameters) => (
                    parameters.name === 'notifications' ?
                        Promise.resolve({ state: Notification.permission }) :
                        originalQuery(parameters)
                );
                
                // Additional anti-detection measures
                window.navigator.chrome = { runtime: {} };
                window.navigator.languages = ['en-US', 'en'];
                
                // Fake plugins and mimeTypes
                Object.defineProperty(navigator, 'plugins', {
                    get: () => [1, 2, 3, 4, 5]
                });
                
                Object.defineProperty(navigator, 'mimeTypes', {
                    get: () => [1, 2, 3, 4, 5]
                });
            """
        })
        
        # Set window size after creation
        driver.set_window_size(1920, 1080)
        
        return driver
    
    @abstractmethod
    def scrape(self, *args, **kwargs) -> pd.DataFrame:
        """Abstract method to be implemented by each scraper."""
        pass
    
    def cleanup(self):
        """Clean up resources."""
        if self.driver:
            self.driver.quit()