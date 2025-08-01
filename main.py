import argparse
import os
from extractor import process_pdfs, extract_and_save
import pdfplumber
from extractors.faq_extractor import FAQExtractor
import json

def main():
    parser = argparse.ArgumentParser(description="Run the PDF scraper and extractor.")
    parser.add_argument("--scrape", action="store_true", help="Run the scraper to fetch PDFs from the website.")
    parser.add_argument("--extract", type=str, help="Run the extractor on a specified local PDF file.")
    parser.add_argument("--pdf-dir", type=str, default="pdfs", help="Directory containing PDFs to process.")
    parser.add_argument("--output-dir", type=str, default="output", help="Directory to save extracted JSON files.")

    args = parser.parse_args()

    if args.scrape:
        from scraper import scrape_pdfs
        scrape_pdfs()
        process_pdfs(args.pdf_dir, args.output_dir)

    if args.extract:
        pdf_path = args.extract
        if not os.path.exists(pdf_path):
            print(f"Error: The file {pdf_path} does not exist.")
            return

        print(f"Processing {pdf_path}...")
        extract_and_save(pdf_path, args.output_dir)

def test_pdf_reading():
    parser = argparse.ArgumentParser(description="Run the PDF scraper and extractor.")
    parser.add_argument("--scrape", action="store_true", help="Run the scraper to fetch PDFs from the website.")
    parser.add_argument("--extract", type=str, help="Run the extractor on a specified local PDF file.")
    parser.add_argument("--pdf-dir", type=str, default="pdfs", help="Directory containing PDFs to process.")
    parser.add_argument("--output-dir", type=str, default="output", help="Directory to save extracted JSON files.")

    args = parser.parse_args()

    pdf_path = args.extract
    if not os.path.exists(pdf_path):
        print(f"Error: The file {pdf_path} does not exist.")
        return

    pdf = pdfplumber.open(pdf_path)

    
    print(pdf.pages[35].extract_text())
    extractor = FAQExtractor()
    extractor.process_page(pdf.pages[35]) # other digital rules
    extractor.process_page(pdf.pages[37]) # bt: gsg
    extractor.process_page(pdf.pages[40]) # bt: warclans
    extractor.finalize()
    # save test data to a file
    output_path = os.path.join(args.output_dir, "test_faq.json")
    with open(output_path, "w") as f:
        json.dump(extractor.get_sections(), f, indent=2)

if __name__ == "__main__":
    main()
    # test_pdf_reading()
