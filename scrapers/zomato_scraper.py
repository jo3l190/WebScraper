import time
import random
import re
from typing import Dict, List, Optional

import pandas as pd
from bs4 import BeautifulSoup
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from .base_scraper import BaseScraper

class ZomatoBakeryScraper(BaseScraper):
    """A class to scrape bakery information from Zomato."""

    # Class constants
    SCROLL_PAUSE_TIME = (1.5, 3.5)
    MAX_SCROLL_ATTEMPTS = 10
    WAIT_TIMEOUT = 10
    
    PRICE_RANGES = [
        (0, 300, 'Budget Friendly'),
        (300, 600, 'Pocket Friendly'),
        (600, 1000, 'Moderate'),
        (1000, 1500, 'Premium'),
        (1500, float('inf'), 'Luxury')
    ]

    def __init__(self, city: str):
        """Initialize Zomato scraper with city name."""
        super().__init__()
        self.city = city.lower()
        self.base_url = f"https://www.zomato.com/{self.city}/bakeries"
        self.driver = self._initialize_driver()
        self.processed_bakeries = set()

    def _wait_for_element(self, by: By, value: str, timeout: Optional[int] = None) -> None:
        """Wait for an element to be present on the page."""
        timeout = timeout or self.WAIT_TIMEOUT
        WebDriverWait(self.driver, timeout).until(
            EC.presence_of_element_located((by, value))
        )

    def _extract_listing_info(self, listing: BeautifulSoup) -> Optional[Dict[str, str]]:
        """Extract information from a single bakery listing."""
        try:
            # Extract name
            name_elem = listing.find('h4')
            if not name_elem:
                return None
            name = name_elem.text.strip()

            # Skip if already processed
            if name in self.processed_bakeries:
                return None
            self.processed_bakeries.add(name)

            # Extract other details
            rating_elem = listing.find('div', class_='sc-1q7bklc-1')
            cost_elem = listing.find('p', class_='KXcjT')
            location_elem = listing.find('p', class_='uIMEk')

            # Create business info dictionary
            return {
                'Name': name,
                'Rating': rating_elem.text.strip() if rating_elem else 'N/A',
                'Cost for Two': cost_elem.text.strip() if cost_elem else 'N/A',
                'Location': location_elem.text.strip() if location_elem else 'N/A'
            }

        except Exception as e:
            print(f"Error extracting listing info: {str(e)}")
            return None

    def _scroll_and_extract_listings(self) -> List[Dict[str, str]]:
        """Scroll through the page and extract all bakery listings."""
        try:
            self.driver.get(self.base_url)
            time.sleep(5)  # Initial load delay
            
            try:
                # Wait for main content to load
                WebDriverWait(self.driver, 20).until(
                    EC.presence_of_element_located((By.CLASS_NAME, "sc-evWYkj"))
                )
            except TimeoutException:
                print("Initial page load timeout, retrying...")
                self.driver.refresh()
                time.sleep(5)
                WebDriverWait(self.driver, 20).until(
                    EC.presence_of_element_located((By.CLASS_NAME, "sc-evWYkj"))
                )

            unique_bakeries = []
            scroll_attempts = 0
            last_height = self.driver.execute_script("return document.body.scrollHeight")

            while scroll_attempts < self.MAX_SCROLL_ATTEMPTS:
                # Scroll down
                self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                time.sleep(random.uniform(*self.SCROLL_PAUSE_TIME))

                # Extract listings
                soup = BeautifulSoup(self.driver.page_source, 'html.parser')
                listings = soup.find_all('div', class_='sc-evWYkj')

                for listing in listings:
                    listing_info = self._extract_listing_info(listing)
                    if listing_info:
                        unique_bakeries.append(listing_info)
                        print(f"Processed: {listing_info['Name']}")

                # Check if scroll reached bottom
                new_height = self.driver.execute_script("return document.body.scrollHeight")
                if new_height == last_height:
                    scroll_attempts += 1
                else:
                    scroll_attempts = 0
                last_height = new_height

            return unique_bakeries

        except Exception as e:
            print(f"Error during scroll and extraction: {str(e)}")
            return []

    @staticmethod
    def _clean_cost(cost: str) -> Optional[int]:
        """Clean cost string to extract numerical value."""
        if pd.isna(cost) or cost == 'N/A':
            return None
        try:
            cleaned = re.sub(r'[^\d,]', '', str(cost))
            return int(cleaned.replace(',', ''))
        except (ValueError, TypeError):
            return None

    @staticmethod
    def _clean_rating(rating: str) -> Optional[float]:
        """Clean rating string to extract numerical value."""
        if pd.isna(rating) or rating == 'N/A':
            return None
        try:
            return float(rating)
        except ValueError:
            return None

    def _categorize_price(self, cost: Optional[float]) -> str:
        """Categorize bakeries based on cost for two."""
        if pd.isna(cost):
            return 'Not Available'

        for min_cost, max_cost, category in self.PRICE_RANGES:
            if min_cost <= cost < max_cost:
                return category
        return 'Not Available'

    def scrape(self) -> pd.DataFrame:
        """
        Main scraping method to collect and process bakery listings.
        
        Returns:
            DataFrame containing bakery information with columns:
            - Name
            - Rating
            - Cost for Two
            - Location
            - Price Category
        """
        try:
            # Collect bakery data
            bakeries = self._scroll_and_extract_listings()
            if not bakeries:
                return pd.DataFrame()

            # Create and clean DataFrame
            df = pd.DataFrame(bakeries)
            
            # Clean numeric columns
            df['Cost for Two'] = df['Cost for Two'].apply(self._clean_cost)
            df['Rating'] = df['Rating'].apply(self._clean_rating)
            
            # Add price category
            df['Price Category'] = df['Cost for Two'].apply(self._categorize_price)

            # Reorder columns
            column_order = [
                'Name', 'Rating', 'Cost for Two', 'Price Category',
                'Location'
            ]
            return df[column_order]

        except Exception as e:
            print(f"Error during scraping: {str(e)}")
            return pd.DataFrame()
        finally:
            self.cleanup()