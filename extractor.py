import os
import json
import pdfplumber
from extractors.faq_extractor import extract_faq_data
from extractors.rules_extractor import extract_rules_data
from extractors.battle_profile_extractor import extract_battle_profile_data
from metadata import create_metadata

def process_pdfs(pdf_dir, output_dir):
    for filename in os.listdir(pdf_dir):
        if filename.endswith('.pdf'):
            pdf_path = os.path.join(pdf_dir, filename)
            print(f"Processing {pdf_path}...")

            extract_and_save(pdf_path, output_dir)

def extract_and_save(pdf_path, output_dir):
    pdf_metadata = create_metadata(pdf_path)

    with pdfplumber.open(pdf_path) as pdf:
        faq_data = extract_faq_data(pdf)
        rules_data = extract_rules_data(pdf)
        battle_profile_data = extract_battle_profile_data(pdf)

    save_to_json(faq_data, os.path.join(output_dir, "faq.json"), {**pdf_metadata, "type": "faq"})
    save_to_json(rules_data, os.path.join(output_dir, "rules.json"), {**pdf_metadata, "type": "rules"})
    save_to_json(battle_profile_data, os.path.join(output_dir, "battleprofile.json"), {**pdf_metadata, "type": "battleprofile"})

def save_to_json(data, output_path, metadata=None):
    if metadata:
        data = {**metadata, "data": data}
    with open(output_path, 'w') as f:
        json.dump(data, f, indent=2)
