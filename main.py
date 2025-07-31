import argparse
import os
import pdfplumber
from extractor import process_pdfs, save_to_json
from extractors.faq_extractor import extract_faq_data
from extractors.rules_extractor import extract_rules_data
from extractors.battle_profile_extractor import extract_battle_profile_data

PDF_DIR = "pdfs"
OUTPUT_DIR = "output"

def main():
    parser = argparse.ArgumentParser(description="Run the PDF scraper and extractor.")
    parser.add_argument("--scrape", action="store_true", help="Run the scraper to fetch PDFs from the website.")
    parser.add_argument("--extract", type=str, help="Run the extractor on a specified local PDF file.")

    args = parser.parse_args()

    if args.scrape:
        from scraper import scrape_pdfs
        scrape_pdfs()
        process_pdfs()

    if args.extract:
        pdf_path = args.extract
        if not os.path.exists(pdf_path):
            print(f"Error: The file {pdf_path} does not exist.")
            return

        print(f"Processing {pdf_path}...")
        with pdfplumber.open(pdf_path) as pdf:
            faq_data = extract_faq_data(pdf)
            rules_data = extract_rules_data(pdf)
            battle_profile_data = extract_battle_profile_data(pdf)

        save_to_json(faq_data, os.path.join(OUTPUT_DIR, "faq.json"))
        save_to_json(rules_data, os.path.join(OUTPUT_DIR, "rules.json"))
        save_to_json(battle_profile_data, os.path.join(OUTPUT_DIR, "battleprofile.json"))

if __name__ == "__main__":
    main()
