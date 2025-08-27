import argparse
import os
from extractor import extract_and_save
import pdfplumber
from extractors.faq_extractor import FAQExtractor
from extractors.battle_profile_extractor import BPExtractor
import json
from downloader import download_pdfs

DOWNLOAD_DIR = "downloads"
OUTPUT_DIR = "output"

def main():
    parser = argparse.ArgumentParser(description="Run the PDF downloader and extractor.")
    parser.add_argument("--pdf-dir", type=str, default=DOWNLOAD_DIR, help="Directory containing PDFs to process.")
    parser.add_argument("--output-dir", type=str, default=OUTPUT_DIR, help="Directory to save extracted JSON files.")

    args = parser.parse_args()

    download_pdfs(args.pdf_dir)

    if not os.path.exists(args.pdf_dir):
        print(f"Error: The directory {args.pdf_dir} does not exist.")
        return

    print(f"Processing {args.pdf_dir}...")
    extract_and_save(args.pdf_dir, args.output_dir)

if __name__ == "__main__":
    main()
