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
                # Get Chrome version and use matching ChromeDriver
                chrome_version = self._get_chrome_version()
                return webdriver.Chrome(
                    service=Service(ChromeDriverManager(version=chrome_version).install()),
                    options=chrome_options
                )
            except Exception as e1:
                print(f"ChromeDriverManager failed: {e1}")
                try:
                    # Try with latest ChromeDriver
                    return webdriver.Chrome(
                        service=Service(ChromeDriverManager().install()),
                        options=chrome_options
                    )
                except Exception as e2:
                    print(f"Latest ChromeDriver failed: {e2}")
                    # Final fallback with system ChromeDriver
                    chrome_options.add_argument("--ignore-certificate-errors")
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

    def _get_chrome_version(self) -> str:
        """Get installed Chrome/Chromium version."""
        try:
            import subprocess
            if platform.system() == "Linux":
                output = subprocess.check_output(['chromium-browser', '--version'])
                version = output.decode('utf-8').split()[1].split('.')[0]
                return f"{version}.0.0.0"
        except Exception as e:
            print(f"Failed to get Chrome version: {e}")
        return "latest"
    
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