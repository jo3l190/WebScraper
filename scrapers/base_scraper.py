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
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--disable-features=NetworkService")
        chrome_options.add_argument("--window-size=1920x1080")
        chrome_options.add_argument("--disable-features=VizDisplayCompositor")
        chrome_options.add_argument('--ignore-certificate-errors')
        
        if platform.system() == "Linux":  # For Streamlit Cloud
            chrome_options.binary_location = "/usr/bin/chromium-browser"
            try:
                service = Service(
                    executable_path="/usr/bin/chromedriver",
                    log_output=os.path.join(os.getcwd(), 'selenium.log')
                )
                driver = webdriver.Chrome(service=service, options=chrome_options)
                return driver
            except Exception as e1:
                print(f"Failed with system chromedriver: {e1}")
                try:
                    # Try with ChromeDriverManager
                    service = Service(ChromeDriverManager().install())
                    driver = webdriver.Chrome(service=service, options=chrome_options)
                    return driver
                except Exception as e2:
                    print(f"Failed with ChromeDriverManager: {e2}")
                    # Last resort - try with minimal configuration
                    return webdriver.Chrome(options=chrome_options)
        else:  # For local development
            try:
                service = Service(ChromeDriverManager().install())
                return webdriver.Chrome(service=service, options=chrome_options)
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