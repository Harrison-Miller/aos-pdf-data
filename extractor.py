import os
import json
import pdfplumber
from extractors.faq_extractor import extract_faq_data
# from extractors.rules_extractor import extract_rules_data  # Not implemented yet
from extractors.battle_profile_extractor import extract_battle_profile_data
from metadata import create_metadata

OVERLAY_DIR = "overlays"

def extract_and_save(download_dir, output_dir, faq=True, bps=True):
    # Load rules_update.pdf and run extract_faq_data
    rules_update_path = os.path.join(download_dir, "rules_update.pdf")
    if os.path.exists(rules_update_path) and faq:
        print(f"Processing FAQ from {rules_update_path}...")
        pdf_metadata = create_metadata(rules_update_path)
        with pdfplumber.open(rules_update_path) as pdf:
            faq_data = extract_faq_data(pdf.pages)
        # Save FAQ output
        os.makedirs(output_dir, exist_ok=True)
        with open(os.path.join(output_dir, "faq.json"), "w") as f:
            json.dump({**pdf_metadata, "type": "faq", "data": faq_data}, f, indent=2)
    else:
        print("rules_update.pdf not found in downloads directory.")

    # Commented out: extract_rules_data (not implemented)
    # rules_data = extract_rules_data(...)
    # with open(os.path.join(OUTPUT_DIR, "rules.json"), "w") as f:
    #     json.dump(rules_data, f, indent=2)

    # For battle profiles, pass the downloads dir to extract_battle_profile_data
    if bps:
        print(f"Processing battle profiles from {download_dir}...")
        battle_profile_data = extract_battle_profile_data(download_dir)
        battle_profiles_data = merge_overlays(OVERLAY_DIR, battle_profile_data)

        with open(os.path.join(output_dir, "battleprofile.json"), "w") as f:
            json.dump({"type": "battleprofile", "data": battle_profile_data}, f, indent=2)

def merge_overlays(overlays_dir, data):
    print("MERGING OVERLAYS")
    print("======================")

    # Load all overlay JSON files
    overlay_files = [f for f in os.listdir(overlays_dir) if f.endswith(".json")]
    overlays = []
    for overlay_file in overlay_files:
        with open(os.path.join(overlays_dir, overlay_file), "r") as f:
            print("Loading overlay:", overlay_file)
            overlay_data = json.load(f)
            overlays.append(overlay_data)

    # Merge overlays with battle profiles
    for o in overlays:
        o_factions = o.get("factions", [])
        for o_faction in o_factions:
            d_factions = data.get("factions", [])
            if o_faction["name"] in [f["name"] for f in d_factions]:
                # get faction
                d_faction = next((f for f in d_factions if f["name"] == o_faction["name"]), None)

                o_bps = o_faction.get("battle_profiles", [])
                for o_bp in o_bps:
                    # Find the corresponding battle profile in the data
                    d_bp = next((bp for bp in data.get("battle_profiles", []) if bp["name"] == o_bp["name"]), None)
                    if d_bp:
                        print("Overriding battle profile:", d_bp["name"], "to ", o_faction["name"])
                        # override battleprofile
                        d_bp = o_bp
                    else:
                        print("Appending new battle profile:", o_bp["name"], "to ", o_faction["name"])
                        # append new battleprofile to data battle_profiles
                        d_faction["battle_profiles"].append(o_bp)
                break
            else:
                # append new faction to data factions
                print("Appending new faction:", o_faction["name"])
                data["factions"].append(o_faction)
                break

    return data

if __name__ == "__main__":
    DOWNLOAD_DIR = "downloads"
    OUTPUT_DIR = "output"
    extract_and_save(DOWNLOAD_DIR, OUTPUT_DIR)

    # download_dir = "downloads"
    # output_dir = "output"
    # rules_update_path = os.path.join(download_dir, "rules_update.pdf")
    # if os.path.exists(rules_update_path):
    #     print(f"Processing FAQ from {rules_update_path}...")
    #     pdf_metadata = create_metadata(rules_update_path)
    #     with pdfplumber.open(rules_update_path) as pdf:
    #         # page = pdf.pages[3]
    #         # im = page.to_image()
    #         # im.draw_rects(page.images)
    #         # im.save("debug.png")
    #         faq_data = extract_faq_data([pdf.pages[4]])
    #     # Save FAQ output
    #     os.makedirs(output_dir, exist_ok=True)
    #     with open(os.path.join(output_dir, "faq.json"), "w") as f:
    #         json.dump({**pdf_metadata, "type": "faq", "data": faq_data}, f, indent=2)
    # else:
    #     print("rules_update.pdf not found in downloads directory.")