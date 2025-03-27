from abc import ABC, abstractmethod
import platform
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
        chrome_options.add_argument("--headless=new")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--window-size=1920,1080")
        chrome_options.add_argument('--disable-blink-features=AutomationControlled')
        
        if platform.system() == "Linux":  # For Streamlit Cloud
            try:
                # Use system Chromium
                chrome_options.binary_location = "/usr/bin/chromium-browser"
                return webdriver.Chrome(
                    options=chrome_options,
                    service=Service('/usr/bin/chromedriver')
                )
            except Exception as e1:
                print(f"System ChromeDriver failed: {e1}")
                try:
                    # Try using ChromeDriverManager
                    return webdriver.Chrome(
                        service=Service(ChromeDriverManager(version="stable").install()),
                        options=chrome_options
                    )
                except Exception as e2:
                    print(f"ChromeDriverManager failed: {e2}")
                    # Final fallback
                    return webdriver.Chrome(options=chrome_options)
        else:  # For local development
            try:
                return webdriver.Chrome(
                    service=Service(ChromeDriverManager().install()),
                    options=chrome_options
                )
            except Exception as e:
                print(f"Local Chrome initialization failed: {e}")
                return webdriver.Chrome(options=chrome_options)
    
    @abstractmethod
    def scrape(self, *args, **kwargs) -> pd.DataFrame:
        """Abstract method to be implemented by each scraper."""
        pass
    
    def cleanup(self):
        """Clean up resources."""
        try:
            if self.driver:
                self.driver.quit()
        except Exception as e:
            print(f"Cleanup failed: {e}")