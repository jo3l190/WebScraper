import pandas as pd
from scrapers.google_maps_scraper import GoogleMapsScraper
import time
from pathlib import Path
import os

def batch_scrape_bakeries(input_file: str = "in.csv") -> None:
    """
    Scrape bakery data for multiple cities from CSV file and combine results.
    
    Args:
        input_file: Path to CSV file containing city names (defaults to 'in.csv')
    """
    # Read cities from CSV
    try:
        cities_df = pd.read_csv(input_file)
        cities = cities_df['city'].dropna().unique()  # Using 'city' column from your CSV
    except Exception as e:
        print(f"Error reading input file: {str(e)}")
        return

    # Create output directory
    output_dir = Path("scraped_results")
    output_dir.mkdir(exist_ok=True)
    
    all_results = []
    failed_cities = []
    
    # Process each city
    total_cities = len(cities)
    for i, city in enumerate(cities, 1):
        print(f"\nProcessing {i}/{total_cities}: {city}")
        
        try:
            # Initialize scraper
            scraper = GoogleMapsScraper()
            
            # Construct search query
            search_query = f"Bakeries in {city}"
            
            # Scrape data
            print(f"Scraping data for: {search_query}")
            df = scraper.scrape(search_query)
            
            if df is not None and not df.empty:
                # Add city column and timestamp
                df['Source City'] = city
                df['Scrape Date'] = pd.Timestamp.now().strftime('%Y-%m-%d %H:%M:%S')
                
                # Save individual city results
                city_file = output_dir / f"bakeries_{city.replace(' ', '_')}.csv"
                df.to_csv(city_file, index=False)
                print(f"Saved results for {city}: {len(df)} bakeries")
                
                # Add to combined results
                all_results.append(df)
            else:
                print(f"No results found for {city}")
                failed_cities.append(city)
                
        except Exception as e:
            print(f"Error processing {city}: {str(e)}")
            failed_cities.append(city)
        
        # Add delay between cities to avoid rate limiting
        time.sleep(5)
        
    # Combine all results
    if all_results:
        combined_df = pd.concat(all_results, ignore_index=True)
        
        # Save combined results with timestamp
        timestamp = time.strftime("%Y%m%d_%H%M%S")
        combined_file = output_dir / f"all_bakeries_{timestamp}.csv"
        combined_df.to_csv(combined_file, index=False)
        
        # Save failed cities list if any
        if failed_cities:
            failed_file = output_dir / f"failed_cities_{timestamp}.txt"
            with open(failed_file, 'w') as f:
                f.write('\n'.join(failed_cities))
        
        print(f"\nProcessing complete!")
        print(f"Total cities processed: {total_cities}")
        print(f"Successful cities: {total_cities - len(failed_cities)}")
        print(f"Failed cities: {len(failed_cities)}")
        print(f"Total bakeries found: {len(combined_df)}")
        print(f"Results saved to: {combined_file}")
        if failed_cities:
            print(f"Failed cities saved to: {failed_file}")
    else:
        print("\nNo results found for any city")

if __name__ == "__main__":
    batch_scrape_bakeries()