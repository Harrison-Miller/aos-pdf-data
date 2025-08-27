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

def extract_bp_tables(page):
    """Extracts lines of text outside tables and tables from a PDF page."""
    page = page.filter(lambda obj: obj.get("text") != " ")
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

    outside_words = [w for w in words if is_outside_tables(w)]

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
    if os.path.exists(battle_profiles_path):
        print(f"PROCESSING BATTLE PROFILES: {battle_profiles_path}")
        print("==================================")
        with pdfplumber.open(battle_profiles_path) as pdf:
            for page in pdf.pages:
                extractor.process_page(page)
    else:
        print(f"Warning: {battle_profiles_path} not found.")
    # Process all faction PDFs
    faction_pattern = os.path.join(pdf_dir, "faction_*_battle_profiles.pdf")
    for faction_pdf in glob.glob(faction_pattern):
        print(f"PROCESSING FACTION: {faction_pdf}")
        print("==================================")
        with pdfplumber.open(faction_pdf) as pdf:
            for page in pdf.pages:
                extractor.process_page(page)
    extractor.finalize()
    return extractor.get_battle_profiles()