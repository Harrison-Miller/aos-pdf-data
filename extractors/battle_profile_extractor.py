from pdfplumber import PDF
import re
from extractors.utils import normalize_text, extract_points
from extractors.regiment_of_renown import RegimentOfRenown
from extractors.battle_profiles import OtherBattleProfile, UnitBattleProfile, FactionBattleProfiles
from extractors.regiment_option import RegimentOption
from extractors.bp_table import determine_table_type
import pdfplumber
import glob
import os
from datetime import datetime

class BPExtractor:
    def __init__(self):
        self.factions = {} # name to FactionBattleProfiles mapping
        self.universal_manifestations = []
        self.regiments_of_renown = []  # List to hold regiments of renown

    def process_page(self, page):
        
        # Extract text and tables from the page
        outside_text, tables = extract_bp_tables(page)
        title = normalize_text(outside_text[3])

        # Process each table to extract battle profile data
        for table in tables:
            table_type = determine_table_type(table)
            if title == "REGIMENTS OF RENOWN":
                for row in table:
                    regiment = RegimentOfRenown(row)
                    if regiment.points > 0:
                        self.regiments_of_renown.append(regiment)
                    else:
                        print(f"Warning: Regiment '{regiment.name}' has no points.")
                continue

            # TODO: handle universal manifestations separately
            if table_type == "universal_manifestations":
                self.process_universal_manifestations(table)
                continue
            if table_type != "unknown":
                if table_type == "legends_units" or table_type == "legends_heroes":
                    maybe_title = table[0][0]
                    if "LEGENDS" in maybe_title:
                        # add a row above with the title
                        table.insert(0, [title])
                    else:
                        title = maybe_title
                if title not in self.factions:
                    self.factions[title] = FactionBattleProfiles(title)
                self.factions[title].process_table(table)

    def process_regiments_of_renown(self, table):
        """Process a table of regiments of renown."""
        print(f"Processing regiments of renown table")
        header = table[0]
        profiles = []
        for row in table[1:]:
            name = normalize_text(row[0].replace('\n', ' ').strip())
            points = extract_points(row[1].strip())
            notes = row[2].strip() if len(row) > 2 else ""
            profiles.append({
                "name": name,
                "points": points
            })
        self.regiments_of_renown.extend(profiles)
    def process_universal_manifestations(self, table):
        """Process a table of universal manifestations."""
        print(f"Processing universal manifestations table")
        header = table[0]
        profiles = []
        for row in table[1:]:
            name = normalize_text(row[0].replace('\n', ' ').strip())
            points = extract_points(row[1].strip())
            profiles.append({
                "name": name,
                "points": points
            })
        self.universal_manifestations.extend(profiles)

    def finalize(self):
        print("Finalizing battle profiles...")
        keywords = []
        unit_names = []
        subhero_categories = []
        for faction in self.factions.values():
            keywords.append(faction.faction_name)  # Add faction name as a keyword
            # Collect keywords, unit names, and subhero categories from all battle profiles
            for profile in faction.battle_profiles.values():
                # print(f"Processing profile: {profile.name}")
                keywords.extend(profile.keywords)
                unit_names.append(profile.name)
                subhero_categories.extend(profile.subhero_categories)

        keywords = sorted(set(keywords), key=lambda x: (-len(x), x.lower()))  # Remove duplicates, sort longest first then alpha
        unit_names = list(set(unit_names))  # Remove duplicates
        subhero_categories = list(set(subhero_categories))  # Remove duplicates
        # units with names like: Name, Title. we want a map of Name to full name
        titled_units = {name.split(",")[0].strip(): name for name in unit_names if "," in name}
        print(f"Collected {len(keywords)} keywords, {len(unit_names)} unit names, {len(titled_units)} title units and {len(subhero_categories)} subhero categories.")
        for faction in self.factions.values():
            # Finalize regiment options for each faction's battle profiles
            for profile in faction.battle_profiles.values():
                profile.finalize_regiment_options(keywords=keywords, unit_names=unit_names, titled_units=titled_units, subhero_categories=subhero_categories)

    def get_battle_profiles(self):
        """Get the extracted battle profiles."""
        return {
            "universal_manifestations": self.universal_manifestations,
            "regiments_of_renown": [reg.to_dict() for reg in self.regiments_of_renown],
            "factions": [faction.to_dict() for faction in self.factions.values()],
        }

def is_strikethrough(word, lines):
    """Detects if a word is striked through by checking if any horizontal line intersects the word's bounding box."""
    x0, top, x1, bottom = word["x0"], word["y0"], word["x1"], word["y1"]
    # Get all horizontal lines on the page
    for line in lines:
        lx0, ly0, lx1, ly1 = line["x0"], line["y0"], line["x1"], line["y1"]
        # Check if line is horizontal (y0 == y1 or very close)
        if abs(ly0 - ly1) <= 1:
            # Check if line horizontally crosses the word's bbox
            if (lx0 <= x1 and lx1 >= x0) and (ly0 >= top and ly0 <= bottom):
                return True
    return False

def extract_bp_tables(page):
    """Extracts lines of text outside tables and tables from a PDF page."""
    # Remove strikethrough text from the page before extracting tables
    lines = page.lines
    def not_strikethrough(obj):
        if obj.get("text") == " ":
            return False
        # Only check for strikethrough if obj has text and bbox
        if "text" in obj and obj["text"] and all(k in obj for k in ["x0", "top", "x1", "bottom"]):
            if is_strikethrough(obj, lines):
                print(f"[DEBUG] Removed strikethrough text before table extraction: '{obj['text']}' at ({obj['x0']},{obj['top']},{obj['x1']},{obj['bottom']})")
                return False
        return True
    page = page.filter(not_strikethrough)
    tables = page.extract_tables(table_settings={"text_x_tolerance": 1})

    # Get all table bbox regions
    table_bboxes = []
    for table in page.find_tables():
        table_bboxes.append(table.bbox)

    # Extract all words with their positions
    words = page.extract_words()

    # Filter words that are NOT inside any table bbox
    def is_outside_tables(word):
        margin = 2  # Add a small margin around table bounding boxes
        x0, top, x1, bottom = word["x0"], word["top"], word["x1"], word["bottom"]
        for bbox in table_bboxes:
            bx0, btop, bx1, bbottom = bbox
            if (x0 >= bx0 - margin and x1 <= bx1 + margin and top >= btop - margin and bottom <= bbottom + margin):
                return False
        return True

    outside_words = []
    for w in words:
        if is_outside_tables(w):
            outside_words.append(w)

    # Group words into lines based on their 'top' coordinate
    lines = []
    current_line = []
    last_top = None
    line_tol = 2 # Tolerance for grouping words into the same line

    for word in sorted(outside_words, key=lambda w: (w["top"], w["x0"])):
        if last_top is None or abs(word["top"] - last_top) > line_tol:
            if current_line:
                lines.append(" ".join(w["text"] for w in current_line))  # Ensure proper spacing
            current_line = [word]
            last_top = word["top"]
        else:
            current_line.append(word)
    if current_line:
        lines.append(" ".join(w["text"] for w in current_line))  # Ensure proper spacing

    return lines, tables

def extract_battle_profile_data(pdf_dir):
    extractor = BPExtractor()
    # Process battle_profiles.pdf
    battle_profiles_path = os.path.join(pdf_dir, "battle_profiles.pdf")
    main_bp_date = None
    if os.path.exists(battle_profiles_path):
        print(f"PROCESSING BATTLE PROFILES: {battle_profiles_path}")
        print("==================================")
        with pdfplumber.open(battle_profiles_path) as pdf:
            main_bp_date = get_published_month_year(pdf)
            for page in pdf.pages:
                extractor.process_page(page)
    else:
        print(f"Warning: {battle_profiles_path} not found.")



    # Process all faction PDFs
    print(f"Main battle profiles published date: {main_bp_date}")
    faction_pattern = os.path.join(pdf_dir, "faction_*_battle_profiles.pdf")
    for faction_pdf in glob.glob(faction_pattern):
        with pdfplumber.open(faction_pdf) as pdf:
            faction_bp_date = get_published_month_year(pdf)
            print(f"Faction battle profiles {faction_pdf} published date: {faction_bp_date}")
            # if faction_bp_date newer the main_bp_date process otherwise skip
            if main_bp_date and faction_bp_date and faction_bp_date < main_bp_date:
                print(f"Skipping {faction_pdf} as it is not newer than main battle profiles.")
                continue

            print(f"PROCESSING FACTION: {faction_pdf}")
            print("==================================")
            for page in pdf.pages:
                extractor.process_page(page)
    extractor.finalize()
    return extractor.get_battle_profiles()

def get_published_month_year(pdf):
    # check first page for a month and year pattern like "January 2024"
    first_page = pdf.pages[0]
    text = first_page.extract_text()
    match = re.search(r"(January|February|March|April|May|June|July|August|September|October|November|December)\s+(\d{4})", text, re.IGNORECASE)
    if match:
        month, year = match.groups()
        # return comparable date object
        return datetime.strptime(f"{month} {year}", "%B %Y")
    return None