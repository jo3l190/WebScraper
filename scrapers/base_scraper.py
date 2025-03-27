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
        
        if platform.system() == "Linux":  # For Streamlit Cloud
            chrome_options.binary_location = "/usr/bin/chromium-browser"
            try:
                return webdriver.Chrome(
                    options=chrome_options
                )
            except Exception as e:
                print(f"Linux Chrome initialization failed: {e}")
                return webdriver.Chrome(
                    service=Service('/usr/bin/chromedriver'),
                    options=chrome_options
                )
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