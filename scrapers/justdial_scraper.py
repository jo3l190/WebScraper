import time
import re
from typing import Dict, List, Optional

import pandas as pd
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from webdriver_manager.chrome import ChromeDriverManager
from .base_scraper import BaseScraper

class JustDialScraper(BaseScraper):
    """Scraper for JustDial business listings."""

    def __init__(self):
        """Initialize JustDial scraper."""
        super().__init__()
        self.driver = self._initialize_justdial_driver()
        self.base_url = "https://www.justdial.com"
        
        # Constants
        self.WAIT_TIMEOUT = 10
        self.PAGE_LOAD_DELAY = 5
        self.CLICK_DELAY = 3

    def _initialize_justdial_driver(self) -> webdriver.Chrome:
        """Initialize Chrome WebDriver with JustDial-specific options."""
        chrome_options = Options()
        chrome_options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64)")
        chrome_options.add_argument("--headless")
        # chrome_options.add_argument("--disable-gpu")
        # chrome_options.add_argument("--no-sandbox")
        # chrome_options.add_argument("--disable-dev-shm-usage")
        # chrome_options.add_argument("--window-size=1920,1080")
        
        if platform.system() == "Linux":  # For Streamlit Cloud
            chrome_options.binary_location = "/usr/bin/chromium-browser"
            driver = webdriver.Chrome(options=chrome_options)
        else:  # For local development
            driver = webdriver.Chrome(
                service=Service(ChromeDriverManager().install()),
                options=chrome_options
            )
        
        driver.maximize_window()
        return driver

    def _click_show_numbers(self) -> None:
        """Click on show number buttons to reveal phone numbers."""
        try:
            numbers = WebDriverWait(self.driver, self.WAIT_TIMEOUT).until(
                EC.presence_of_all_elements_located((By.CLASS_NAME, "shownum"))
            )
            for number in numbers:
                try:
                    number.click()
                except:
                    continue
            time.sleep(self.CLICK_DELAY)
        except TimeoutException:
            print("No phone numbers found to click.")

    def _extract_store_details(self, element) -> Optional[Dict[str, str]]:
        """Extract information from a single store listing."""
        try:
            outer_html_text = element.get_attribute("outerHTML")
            soup = BeautifulSoup(outer_html_text, "lxml")

            # Extract store name
            name_elem = soup.find("h2", class_="store-name")
            if not name_elem or not name_elem.span or not name_elem.span.a:
                return None
            store_name = name_elem.span.a.text.strip()

            # Extract other details
            address_elem = soup.find("span", class_="cont_fl_addr")
            address = address_elem.text.strip() if address_elem else "N/A"

            ratings_info = soup.find("p", class_="newrtings")
            rating = "N/A"
            rating_count = "0"
            if ratings_info:
                rating_box = ratings_info.find("span", class_="green-box")
                rating = rating_box.text.strip() if rating_box else "N/A"
                
                count_elem = ratings_info.find("span", class_="rt_count")
                if count_elem:
                    count_match = re.search(r'\d+', count_elem.text.strip())
                    rating_count = count_match.group() if count_match else "0"

            phone_elem = soup.find("p", class_="contact-info")
            phone_no = phone_elem.text.strip() if phone_elem else "N/A"

            return {
                "Store Name": store_name,
                "Address": address,
                "Rating": rating,
                "Rating Count": rating_count,
                "Phone Number": phone_no
            }
        except Exception as e:
            print(f"Error extracting store details: {str(e)}")
            return None

    def _go_to_next_page(self) -> bool:
        """Navigate to the next page of results."""
        try:
            next_page = WebDriverWait(self.driver, 10).until(
                EC.element_to_be_clickable((By.XPATH, "//a[@rel='next']"))
            )
            next_page.click()
            time.sleep(self.PAGE_LOAD_DELAY)
            return True
        except Exception as e:
            print(f"Error: Unable to navigate to the next page. {str(e)}")
            return False

    @staticmethod
    def _clean_rating(rating: str) -> Optional[float]:
        """Clean rating string to float."""
        try:
            return float(rating.replace('/5', '').strip())
        except (ValueError, AttributeError):
            return None

    @staticmethod
    def _clean_rating_count(count: str) -> Optional[int]:
        """Clean rating count string to integer."""
        try:
            return int(''.join(filter(str.isdigit, count)))
        except (ValueError, TypeError):
            return None

    @staticmethod
    def _clean_phone(phone: str) -> str:
        """Clean phone number string."""
        return ''.join(filter(str.isdigit, phone))

    def scrape(self, query: str, num_pages: int = 2) -> pd.DataFrame:
        """
        Main scraping method for JustDial listings.
        
        Args:
            query: Search query for businesses
            num_pages: Number of pages to scrape
            
        Returns:
            DataFrame containing business information
        """
        try:
            self.driver.get(self.base_url)
            
            # Search
            try:
                search_box = WebDriverWait(self.driver, self.WAIT_TIMEOUT).until(
                    EC.presence_of_element_located((By.CLASS_NAME, "input_search"))
                )
                search_box.clear()
                search_box.send_keys(query)
                search_box.send_keys(Keys.RETURN)
                time.sleep(self.PAGE_LOAD_DELAY)
            except:
                print("Search box not found or Justdial blocked the request.")
                return pd.DataFrame()

            store_data = []
            
            for page in range(num_pages):
                try:
                    print(f"Processing page {page + 1}")
                    
                    # Click show numbers
                    self._click_show_numbers()

                    # Extract store details
                    store_elements = self.driver.find_elements(By.CLASS_NAME, "store-details")
                    if not store_elements:
                        print(f"No results found on page {page + 1}")
                        break

                    for element in store_elements:
                        store_info = self._extract_store_details(element)
                        if store_info:
                            store_data.append(store_info)
                            print(f"Processed: {store_info['Store Name']}")

                    if page < num_pages - 1:
                        if not self._go_to_next_page():
                            print(f"No more pages available after page {page + 1}")
                            break

                except Exception as e:
                    print(f"Error processing page {page + 1}: {str(e)}")
                    break

            # Create DataFrame and clean data
            df = pd.DataFrame(store_data)
            if not df.empty:
                # Clean data
                df['Rating'] = df['Rating'].apply(self._clean_rating)
                df['Rating Count'] = df['Rating Count'].apply(self._clean_rating_count)
                df['Phone Number'] = df['Phone Number'].apply(self._clean_phone)
                
                # Remove duplicates based on both name and address
                total_before = len(df)
                df = df.drop_duplicates(subset=['Store Name', 'Address'], keep='first')
                duplicates_removed = total_before - len(df)
                
                print(f"Total listings found: {total_before}")
                print(f"Duplicates removed: {duplicates_removed}")
                print(f"Final unique listings: {len(df)}")

            return df

        except Exception as e:
            print(f"Fatal error occurred: {str(e)}")
            return pd.DataFrame()
        finally:
            self.cleanup()