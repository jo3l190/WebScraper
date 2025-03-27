import time
from typing import Dict, List, Optional
import pandas as pd
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException, StaleElementReferenceException
from bs4 import BeautifulSoup
from .base_scraper import BaseScraper

class GoogleMapsScraper(BaseScraper):
    """Scraper for Google Maps listings."""

    def __init__(self):
        """Initialize Google Maps scraper."""
        super().__init__()
        self.driver = self._initialize_driver()
        self.base_url = "https://www.google.com/maps"
        self.processed_names = set()
        
        # Constants
        self.SCROLL_PAUSE_TIME = 2
        self.MAX_SCROLL_ATTEMPTS = 10
        self.WAIT_TIMEOUT = 10
        self.DETAIL_TIMEOUT = 7

    def _search_location(self, query: str) -> None:
        """Perform search on Google Maps."""
        try:
            search_box = WebDriverWait(self.driver, self.WAIT_TIMEOUT).until(
                EC.presence_of_element_located((By.ID, "searchboxinput"))
            )
            search_box.clear()
            search_box.send_keys(query)
            search_box.send_keys(Keys.RETURN)

            # Wait for search results
            WebDriverWait(self.driver, self.WAIT_TIMEOUT).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "div[role='feed']"))
            )
        except TimeoutException as e:
            print(f"Timeout during search: {str(e)}")
            raise

    def _load_more_results(self) -> List:
        """Load more results by scrolling."""
        try:
            scrollable_div = self.driver.find_element(By.CSS_SELECTOR, "div[role='feed']")
            current_count = len(self.driver.find_elements(By.CSS_SELECTOR, "div.Nv2PK"))
            
            # Try scrolling a few times
            for _ in range(3):
                self.driver.execute_script(
                    "arguments[0].scrollTo(0, arguments[0].scrollHeight);",
                    scrollable_div
                )
                time.sleep(0.5)
            
            # Check if we got new results
            new_count = len(self.driver.find_elements(By.CSS_SELECTOR, "div.Nv2PK"))
            
            # If no new results after scrolling, check for end of list
            if new_count <= current_count:
                try:
                    end_message = self.driver.find_element(
                        By.XPATH, 
                        "//span[contains(text(), 'reached the end') or contains(text(), 'No more results')]"
                    )
                    if end_message:
                        print("Reached end of results list")
                        return []
                except NoSuchElementException:
                    pass

            time.sleep(self.SCROLL_PAUSE_TIME)
            return self.driver.find_elements(By.CSS_SELECTOR, "div.Nv2PK")
            
        except Exception as e:
            print(f"Error loading more results: {str(e)}")
            return []

    def _extract_basic_info(self, soup: BeautifulSoup) -> Dict[str, str]:
        """Extract basic information from listing."""
        name_tag = soup.find("div", class_="qBF1Pd")
        rating_tag = soup.find("span", class_="MW4etd")
        rating_count_tag = soup.find("span", class_="UY7F9")
        
        name = name_tag.text.strip() if name_tag else "N/A"
        rating = rating_tag.text.strip() if rating_tag else "N/A"
        rating_count = rating_count_tag.text.strip() if rating_count_tag else "N/A"
        
        category = "N/A"
        category_divs = soup.find_all("div", class_="W4Efsd")
        for div in category_divs:
            span_tag = div.find("span", recursive=False)
            if span_tag and span_tag.text.strip():
                category = span_tag.text.strip()
                break
                
        return {
            "Name": name,
            "Rating": rating,
            "Rating Count": rating_count,
            "Category": category
        }

    def _extract_details(self, result) -> Dict[str, str]:
        """Extract detailed information from listing."""
        try:
            clickable = result.find_element(By.CSS_SELECTOR, "a.hfpxzc")
            self.driver.execute_script("arguments[0].click();", clickable)
            
            details_panel = WebDriverWait(self.driver, self.DETAIL_TIMEOUT).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "div.m6QErb.tLjsW"))
            )
            time.sleep(1.5)

            # Extract phone number
            try:
                phone_element = WebDriverWait(self.driver, 2).until(
                    EC.presence_of_element_located((By.XPATH,
                        '//button[contains(@data-item-id, "phone:tel:")]//div[contains(@class, "fontBodyMedium")]'))
                )
                phone_number = phone_element.text.strip()
            except (TimeoutException, NoSuchElementException):
                phone_number = "N/A"

            # Extract address
            try:
                address_element = WebDriverWait(self.driver, 2).until(
                    EC.presence_of_element_located((By.XPATH,
                        '//button[@data-item-id="address"]//div[contains(@class, "fontBodyMedium")]'))
                )
                address = address_element.text.strip()
            except (TimeoutException, NoSuchElementException):
                address = "N/A"

            return {
                "Full Address": address,
                "Phone Number": phone_number
            }
        finally:
            # Return to results list
            self.driver.find_element(By.TAG_NAME, "body").send_keys(Keys.ESCAPE)
            time.sleep(1)

    def scrape(self, query: str, num_results: int = 10) -> pd.DataFrame:
        """Main scraping method to collect and process Google Maps listings."""
        try:
            self.driver.get(self.base_url)
            self._search_location(query)

            places_data = []
            scroll_attempts = 0
            results = self._load_more_results()
            last_count = 0

            while len(places_data) < num_results and scroll_attempts < self.MAX_SCROLL_ATTEMPTS:
                if not results:
                    # Check if we're truly at the end
                    current_count = len(places_data)
                    if current_count == last_count:
                        scroll_attempts += 1
                        if scroll_attempts >= 3:  # Give up after 3 attempts with no new results
                            print(f"No more results available. Found {len(places_data)} places.")
                            break
                    else:
                        last_count = current_count
                        scroll_attempts = 0
                    
                    results = self._load_more_results()
                    continue

                batch_size = min(5, num_results - len(places_data))
                current_batch = results[:batch_size]
                results = results[batch_size:]

                for result in current_batch:
                    try:
                        # Extract basic information
                        soup = BeautifulSoup(result.get_attribute("outerHTML"), "lxml")
                        basic_info = self._extract_basic_info(soup)
                        
                        if basic_info["Name"] in self.processed_names or basic_info["Name"] == "N/A":
                            continue
                        self.processed_names.add(basic_info["Name"])

                        # Extract detailed information
                        detailed_info = self._extract_details(result)
                        
                        # Combine information
                        place_info = {**basic_info, **detailed_info}
                        places_data.append(place_info)

                        print(f"Processed: {place_info['Name']} ({len(places_data)}/{num_results})")

                        if len(places_data) >= num_results:
                            break

                    except Exception as e:
                        print(f"Error processing result: {str(e)}")
                        continue

            print(f"Scraping completed. Found {len(places_data)} places.")
            df = pd.DataFrame(places_data)
            
            # Clean numeric data
            if not df.empty:
                df['Rating'] = df['Rating'].apply(self.clean_rating)
                df['Rating Count'] = df['Rating Count'].apply(self.clean_rating_count)
            
            return df

        except Exception as e:
            print(f"Fatal error occurred: {str(e)}")
            return pd.DataFrame()
        finally:
            self.cleanup()

    @staticmethod
    def clean_rating(rating: str) -> Optional[float]:
        """Clean rating string to float."""
        try:
            return float(rating)
        except (ValueError, TypeError):
            return None

    @staticmethod
    def clean_rating_count(count: str) -> Optional[int]:
        """Clean rating count string to integer."""
        try:
            return int(''.join(filter(str.isdigit, count)))
        except (ValueError, TypeError):
            return None