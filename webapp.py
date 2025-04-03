import streamlit as st
import pandas as pd
from io import BytesIO
from scrapers.justdial_scraper import JustDialScraper
from scrapers.google_maps_scraper import GoogleMapsScraper
from scrapers.zomato_scraper import ZomatoBakeryScraper

def download_results(df: pd.DataFrame, filename: str) -> None:
    """Create a download button for DataFrame results."""
    csv_buffer = BytesIO()
    df.to_csv(csv_buffer, index=False)
    csv_buffer.seek(0)
    st.download_button(
        "Download CSV",
        csv_buffer,
        filename,
        "text/csv"
    )

st.title("Web Scraper")
st.write("Choose a platform and enter search details")

# Option to select scraper
scraper_option = st.radio(
    "Select Scraper:",
    ("Justdial", "Google Maps", "Zomato Bakeries")
)

if scraper_option == "Justdial":
    query = st.text_input("Enter search query:", "")
    num_pages = st.number_input("Number of pages to scrape:", min_value=1)

    if st.button("Scrape Data"):
        if query:
            with st.spinner("Scraping data..."):
                try:
                    scraper = JustDialScraper()
                    df = scraper.scrape(query, num_pages)
                    
                    if df is not None and not df.empty:
                        st.success("Scraping completed successfully!")
                        st.dataframe(df)
                        download_results(df, "justdial_results.csv")
                    else:
                        st.warning("No data found.")
                except Exception as e:
                    st.error(f"An error occurred: {str(e)}")
        else:
            st.warning("Please enter a search query.")

elif scraper_option == "Google Maps":
    st.info("Note: Google Maps typically returns a maximum of 100-115 results per query.")
    
    query = st.text_input("Enter search query:", "")
    
    # Add radio button to choose between limited and all results
    scrape_option = st.radio(
        "Scraping Option:",
        ("Limited Results", "All Available Results")
    )
    
    # Show number input only for limited results option
    num_results = None
    if scrape_option == "Limited Results":
        num_results = st.number_input("Number of results:", min_value=1, max_value=115)
    
    min_rating = st.slider(
        "Minimum Rating:",
        min_value=0.0,
        max_value=5.0,
        value=0.0,
        step=0.1
    )

    if st.button("Scrape Data"):
        if query:
            with st.spinner("Scraping data... This may take a while for all results"):
                try:
                    scraper = GoogleMapsScraper()
                    # Pass None as num_results to get all available data
                    df = scraper.scrape(query, num_results) if num_results else scraper.scrape(query)
                    
                    if df is not None and not df.empty:
                        st.success("Scraping completed successfully!")

                        # Filter by minimum rating
                        if min_rating > 0:
                            filtered_df = df[df['Rating'] >= min_rating]
                            
                            # Show filtered results info
                            st.write(
                                f"Showing {len(filtered_df)} results with rating ≥ "
                                f"{min_rating} (out of {len(df)} total)"
                            )
                            
                            # Display filtered results
                            st.dataframe(filtered_df)
                            download_results(
                                filtered_df,
                                "google_maps_filtered_results.csv"
                            )
                        else:
                            # Show all results if no minimum rating
                            st.dataframe(df)
                            download_results(df, "google_maps_results.csv")
                    else:
                        st.warning("No data found.")
                except Exception as e:
                    st.error(f"An error occurred: {str(e)}")
        else:
            st.warning("Please enter a search query.")

elif scraper_option == "Zomato Bakeries":
    city = st.text_input("Enter city name:", "")
    
    # Add price category information
    st.info("""
    Price Categories:
    - Budget Friendly: Less than ₹300
    - Pocket Friendly: ₹300 – ₹599  
    - Moderate: ₹600 – ₹999
    - Premium: ₹1,000 – ₹1,499
    - Luxury: ₹1,500 and above
    """)
    
    # Price category selection
    price_categories = st.multiselect(
        "Select Price Categories:",
        options=[
            "Budget Friendly",
            "Pocket Friendly", 
            "Moderate",
            "Premium",
            "Luxury"
        ],
        default=["Budget Friendly", "Pocket Friendly", "Moderate"]
    )

    if st.button("Scrape Zomato Bakeries"):
        if city:
            with st.spinner("Scraping Zomato Bakeries..."):
                try:
                    scraper = ZomatoBakeryScraper(city)
                    df = scraper.scrape()

                    if df is not None and not df.empty:
                        # Filter by selected price categories
                        filtered_df = df[df['Price Category'].isin(price_categories)]

                        st.success(f"Scraped {len(df)} bakeries in {city}!")
                        
                        # Show filtered results info
                        st.write(
                            f"Showing {len(filtered_df)} results in selected price "
                            f"categories (out of {len(df)} total)"
                        )

                        # Display filtered results
                        st.dataframe(filtered_df)
                        download_results(
                            filtered_df,
                            f"{city}_zomato_bakeries.csv"
                        )
                    else:
                        st.warning("No bakeries found.")
                except Exception as e:
                    st.error(f"An error occurred: {str(e)}")
        else:
            st.warning("Please enter a city name.")