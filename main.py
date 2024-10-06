from Miner.AutoScout24Scraper import AutoScout24Scraper
from Analysis.DataProcessor import DataProcessor
from Analysis.MileagePriceRegression import MileagePriceRegression
from Miner.TextFileHandler import TextFileHandler

import os
import argparse


def main(scrape=False, make=None, model=None, version="", year_from=None, year_to=None,
         power_from="", power_to="", powertype="kw", num_pages=20, zipr=600, zip_list_file_path="Miner/capoluoghi.csv",
         downloaded_listings_file="", output_file_preprocessed=""):
    
    zip_list = where_to_search(zip_list_file_path)
    
    # Scraping the data if scrape is set to True
    if scrape:
        scrape_autoscout(zip_list, make, model, version, year_from, year_to, power_from, power_to, powertype, num_pages, zipr, downloaded_listings_file)
    
    # Data Processing
    data_preprocessed = preprocess(downloaded_listings_file, output_file_preprocessed)
    
    # Mileage-Price Regression
    perform_regression(data_preprocessed)


def perform_regression(data_preprocessed):
    grouped_data = data_preprocessed.groupby('mileage_grouped')['price'].agg(['mean', 'std']).reset_index()
    mileage_values = grouped_data['mileage_grouped']
    average_price_values = grouped_data['mean']
    std_deviation_values = grouped_data['std']
    regression = MileagePriceRegression(mileage_values, average_price_values, std_deviation_values)
    predicted_prices, best_degree = regression.do_regression()
    
    # Mileage-Price Plotting
    regression.plot_mileage_price(predicted_prices, best_degree)


def preprocess(downloaded_listings_file, output_file_preprocessed):
    processor = DataProcessor(downloaded_listings_file)
    data = processor.read_data()
    data_no_duplicates = processor.remove_duplicates(data)
    data_preprocessed = processor.preprocess_data(data_no_duplicates)
    data_rounded = processor.round(data_preprocessed, 1000)
    processor.save_processed_data(data_rounded, output_file_preprocessed)
    return data_preprocessed


def scrape_autoscout(zip_list, make, model, version, year_from, year_to, power_from, power_to, powertype, num_pages, zipr, downloaded_listings_file):
    scraper = AutoScout24Scraper(make, model, version, year_from, year_to, power_from, power_to, powertype, zip_list, zipr)
    scraper.scrape(num_pages, True)
    scraper.save_to_csv(downloaded_listings_file)
    scraper.quit_browser()


def where_to_search(zip_list_file_path):
    handler = TextFileHandler(zip_list_file_path)
    handler.load_data_csv()
    zip_list = handler.export_capoluogo_column()
    zip_list = [item.lower() for item in zip_list]
    return zip_list


if __name__ == "__main__":
    # Using argparse to handle command line arguments
    parser = argparse.ArgumentParser(description="AutoScout24 Scraper and Mileage-Price Regression Tool")
    
    parser.add_argument("--scrape", action="store_true", help="Flag to indicate whether to scrape data from AutoScout24")
    parser.add_argument("--make", type=str, required=True, help="Car make (required)")
    parser.add_argument("--model", type=str, required=True, help="Car model (required)")
    parser.add_argument("--version", type=str, default="", help="Car version")
    parser.add_argument("--year_from", type=str, required=True, help="Starting year (required)")
    parser.add_argument("--year_to", type=str, required=True, help="Ending year (required)")
    parser.add_argument("--power_from", type=str, default="", help="Power from")
    parser.add_argument("--power_to", type=str, default="", help="Power to")
    parser.add_argument("--powertype", type=str, default="kw", help="Power type")
    parser.add_argument("--num_pages", type=int, default=20, help="Number of pages to scrape")
    parser.add_argument("--zipr", type=int, default=600, help="Radius for zip code search")
    parser.add_argument("--zip_list_file_path", type=str, default="Miner/capoluoghi.csv", help="Path to the zip list file")
    parser.add_argument("--downloaded_listings_file", type=str, default="", help="File to save scraped listings")
    parser.add_argument("--output_file_preprocessed", type=str, default="", help="File to save preprocessed listings data")
    
    args = parser.parse_args()

    # Default file paths for saving scraped data and preprocessed data
    if not args.downloaded_listings_file:
        args.downloaded_listings_file = f'listings/listings_{args.make}_{args.model}.csv'
    if not args.output_file_preprocessed:
        args.output_file_preprocessed = f'listings/listings_{args.make}_{args.model}_preprocessed.csv'

    # Create the "listings" folder if it doesn't exist
    if not os.path.exists("listings"):
        os.makedirs("listings")

    main(scrape=args.scrape, make=args.make, model=args.model, version=args.version, year_from=args.year_from, 
         year_to=args.year_to, power_from=args.power_from, power_to=args.power_to, powertype=args.powertype, 
         num_pages=args.num_pages, zipr=args.zipr, zip_list_file_path=args.zip_list_file_path, 
         downloaded_listings_file=args.downloaded_listings_file, output_file_preprocessed=args.output_file_preprocessed)
