import os
import shutil
import logging
import requests

API_URL = "https://www.warhammer-community.com/api/search/downloads/"
PDF_BASE_URL = "https://assets.warhammer-community.com/"

logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s: %(message)s')

def reset_downloads_dir(download_dir):
    if os.path.exists(download_dir):
        logging.info(f"Deleting existing '{download_dir}' directory.")
        shutil.rmtree(download_dir)
    logging.info(f"Creating '{download_dir}' directory.")
    os.makedirs(download_dir)

def download_file(url, filename, download_dir):
    logging.info(f"Downloading {filename} from {url}")
    response = requests.get(url)
    response.raise_for_status()
    with open(os.path.join(download_dir, filename), "wb") as f:
        f.write(response.content)
    logging.info(f"Saved {filename}")

def get_api_pdfs():
    payload = {
        "index": "downloads_v2",
        "searchTerm": "",
        "gameSystem": "warhammer-age-of-sigmar",
        "language": "english"
    }
    logging.info(f"Fetching PDF metadata from API: {API_URL}")
    response = requests.post(API_URL, json=payload)
    response.raise_for_status()
    data = response.json()
    hits = data.get("hits", [])
    logging.info(f"Found {len(hits)} PDF entries from API.")
    return hits

def download_pdfs(download_dir):
    reset_downloads_dir(download_dir)
    pdfs = get_api_pdfs()
    # Download rules update
    found_rules_update = False
    for pdf in pdfs:
        title = pdf.get("title", "").lower()
        file_id = pdf.get("id", {})
        file_name = file_id.get("file")
        if not file_name:
            continue
        if "rules update" in title:
            url = PDF_BASE_URL + file_name
            download_file(url, "rules_update.pdf", download_dir)
            found_rules_update = True
            break
    if not found_rules_update:
        logging.warning("No rules update PDF found.")
    # Download battle profiles summary
    found_battle_profiles = False
    for pdf in pdfs:
        title = pdf.get("title", "").lower()
        file_id = pdf.get("id", {})
        file_name = file_id.get("file")
        if not file_name:
            continue
        if "battle profiles" == title:
            url = PDF_BASE_URL + file_name
            download_file(url, "battle_profiles.pdf", download_dir)
            found_battle_profiles = True
            break
    if not found_battle_profiles:
        logging.warning("No battle profiles PDF found.")
    # Download faction battle profiles
    faction_count = 0
    for pdf in pdfs:
        title = pdf.get("title", "")
        file_id = pdf.get("id", {})
        file_name = file_id.get("file")
        if not file_name:
            continue
        if "battle profiles" in title.lower() and "faction pack:" not in title.lower() and "battle profiles" != title.lower():
            # Extract faction name
            faction = title.lower().replace("battle profiles","").replace("faction pack:","").replace("faction","").replace("pack:","").replace(".pdf","").strip().replace(" ", "_")
            if faction:
                filename = f"faction_{faction}_battle_profiles.pdf"
                url = PDF_BASE_URL + file_name
                download_file(url, filename, download_dir)
                faction_count += 1
    logging.info(f"Downloaded {faction_count} faction battle profiles PDFs.")

    # Throw error if any required file is missing
    errors = []
    if not found_rules_update:
        errors.append("rules_update.pdf not found")
    if not found_battle_profiles:
        errors.append("battle_profiles.pdf not found")
    if faction_count == 0:
        errors.append("No faction battle profiles PDFs found")
    if errors:
        raise RuntimeError("Required downloads missing: " + ", ".join(errors))

if __name__ == "__main__":
    download_pdfs("downloads")
