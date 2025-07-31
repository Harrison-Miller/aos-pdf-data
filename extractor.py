import os
import json
import pdfplumber
from extractors.faq_extractor import extract_faq_data
from extractors.rules_extractor import extract_rules_data
from extractors.battle_profile_extractor import extract_battle_profile_data

PDF_DIR = "pdfs"
OUTPUT_DIR = "output"

os.makedirs(OUTPUT_DIR, exist_ok=True)

def process_pdfs():
    for filename in os.listdir(PDF_DIR):
        if filename.endswith('.pdf'):
            pdf_path = os.path.join(PDF_DIR, filename)
            print(f"Processing {pdf_path}...")

            with pdfplumber.open(pdf_path) as pdf:
                faq_data = extract_faq_data(pdf)
                rules_data = extract_rules_data(pdf)
                battle_profile_data = extract_battle_profile_data(pdf)

            save_to_json(faq_data, os.path.join(OUTPUT_DIR, "faq.json"))
            save_to_json(rules_data, os.path.join(OUTPUT_DIR, "rules.json"))
            save_to_json(battle_profile_data, os.path.join(OUTPUT_DIR, "battleprofile.json"))

def save_to_json(data, output_path):
    with open(output_path, 'w') as f:
        json.dump(data, f, indent=2)
