from pdfplumber import PDF
import re
from extractors.utils import normalize_text

class OtherBattleProfile:
    def __init__(self, name):
        self.name = normalize_text(name.replace('\n', ' ').strip())
        self.type = None
        self.points = None
        self.notes = None

    def process_row(self, header, row):
        """Process a row to extract other battle profile data."""
        if "TYPE" in header:
            self.type = row[header.index("TYPE")]
        if "POINTS" in header:
            self.points = row[header.index("POINTS")]
        if "NOTES" in header:
            self.notes = row[header.index("NOTES")]

    def to_dict(self):
        return {
            "name": self.name,
            "type": self.type,
            "points": self.points,
            "notes": self.notes
        }

class RegimentOption:
    def __init__(self, line, keywords=[], unit_names=[], titled_units={}, subhero_categories=[]):
        line = normalize_text(line.strip())
        self.line = line
        self.min = 0
        self.max = 0

        if line.startswith("Any"):
            self.max = -1
            line = line.split("Any")[1].strip()  # Remove "Any" prefix

        # regex x-y
        match = re.match(r"(\d+)-(\d+)", line)
        if match:
            self.min = int(match.group(1))
            self.max = int(match.group(2))
            line = line[match.end():].strip()  # Remove the matched part

        if line.endswith("(required)"):
            self.min = 1
            self.max = 1
            line = line.split("(required)")[0].strip()  # Remove "(required)" suffix

        parts = [line]
        if " or " in line:
            parts = line.split(" or ")

        self.keywords = []
        self.nonKeywords = []
        self.subhero_category = ""
        self.unit_name = ""

        for part in parts:
            part = part.strip()
            # check subhero categories
            if any(cat.lower() == part.lower() for cat in subhero_categories):
                self.subhero_category = part
            # check unit names
            elif any(name.lower() == part.lower() for name in unit_names):
                self.unit_name = part
            elif any(name.lower() == part.lower() for name in titled_units):
                # Find the matching titled unit key and get its full name
                for key in titled_units:
                    if key.lower() == part.lower():
                        full_name = titled_units[key]
                        self.unit_name = full_name
                        break
            else:
                # try non-keywords first
                # check lower
                if part.startswith("non-"):
                    k = part[4:].strip()
                    if any(k.lower() == kw.lower() for kw in keywords):
                        self.nonKeywords.append(k)

                # try whole keyword match
                if any(kw.lower() == part.lower() for kw in keywords):
                    self.keywords.append(part)
                else:
                    # try multiple keywords
                    kw_parts = part.split()
                    for kw in kw_parts:
                        if kw.startswith("non-"):
                            kw = kw[4:].strip()
                            if any(kw.lower() == k.lower() for k in keywords):
                                self.nonKeywords.append(kw)

                        if any(kw.lower() == k.lower() for k in keywords):
                            self.keywords.append(kw.strip())

    def valid(self):
        return (self.max == -1 or self.max > 0) and (self.keywords or self.nonKeywords or self.subhero_category or self.unit_name)

    def to_dict(self):
        return {
            "min": self.min,
            "max": self.max,
            "keywords": self.keywords,
            "nonKeywords": self.nonKeywords,
            "subhero_category": self.subhero_category,
            "unit_name": self.unit_name
        }

    

class UnitBattleProfile:
    def __init__(self, name):
        self.name = name
        self.unit_size = None
        self.points = None
        self.keywords = []
        self.regiment_option_lines = []
        self.regiment_options = []
        self.notes = []
        self.base_size = None
        self.subhero_categories = []  # Initialize subhero categories
        self.reinforceable = self.unit_size != 1
        self.requiredLeader = ""
        self.undersizeCondition = ""
        self.retiringOn = ""
        self.exclusiveWith = ""
        self.legends = False

    def process_row(self, header, row):
        """Process a row to extract unit battle profile data."""
        if "UNIT SIZE" in header and row[header.index("UNIT SIZE")]:
            self.unit_size = row[header.index("UNIT SIZE")]
        if "POINTS" in header and row[header.index("POINTS")]:
            self.points = row[header.index("POINTS")]
        if "RELEVANT KEYWORDS" in header and row[header.index("RELEVANT KEYWORDS")]:
            self.keywords = row[header.index("RELEVANT KEYWORDS")].split(",")
            self.keywords = [kw.strip() for kw in self.keywords if kw.strip()]
        if "REGIMENT OPTIONS" in header and row[header.index("REGIMENT OPTIONS")]:
            self.regiment_option_lines = row[header.index("REGIMENT OPTIONS")].split(",")
            self.regiment_option_lines = [opt.strip() for opt in self.regiment_option_lines if opt.strip()]
        if "NOTES" in header and row[header.index("NOTES")]:
            self.notes = normalize_text(row[header.index("NOTES")].replace('\n', ' ').strip()).split(".")
            self.notes = [note.strip() for note in self.notes if note.strip()]
            self.handle_notes()
        if "BASE SIZE" in header and row[header.index("BASE SIZE")]:
            self.base_size = normalize_text(row[header.index("BASE SIZE")].replace('\n', ' ').strip())

    def handle_notes(self):
        for n in self.notes:
            processed = False
            if n.startswith("This Hero can join an eligible regiment as"):
                # Extract the subhero name from the note
                parts = re.split(r"This Hero can join an eligible regiment as(?: (?:a|an))? ", n)
                if len(parts) > 1:
                    processed = True
                    self.subhero_categories.append(parts[1].strip())

            if n == "This unit cannot be reinforced":
                processed = True
                self.reinforceable = False

            if n.startswith("This Hero can join"):
                # This is handled by the regiment options of the leader that can take this unit
                processed = True

            # required leader note: This unit can only be taken in Callis and Toll's regiment
            if n.startswith("This unit can only be taken in"):
                match = re.search(r"This unit can only be taken in (.+?)(?:'s)? regiment", n)
                if match:
                    processed = True
                    self.requiredLeader = match.group(1).strip()

            if "This unit is legal for Matched Play for battles fought using the General's Handbook 2025-26 battlepack" in n and "Scourge of Ghyran" in self.name:
                processed = True

            if n.startswith("This unit can be reinforced"):
                reinforceable = True
                processed = True

            # undersize unit condition:  You can include 1 unit of this type for each LordCelestant on Dracoth in your army
            # we want Lord Celestant on Dracoth
            if n.startswith("You can include 1 unit of this type for each"):
                match = re.search(r"You can include 1 unit of this type for each (.+?) in your army", n)
                if match:
                    self.undersizeCondition = match.group(1).strip()
                    processed = True

            if n.startswith("This unit will move to Warhammer Legends on"):
                match = re.search(r"This unit will move to Warhammer Legends on (.+)", n)
                if match:
                    self.retiringOn = match.group(1).strip()
                    processed = True

            # exclusive with condition: You cannot include this unit and Cado Ezechiar, the Hollow King in the same army
            if n.startswith("You cannot include this unit and "):
                match = re.search(r"You cannot include this unit and (.+?) in the same army", n)
                if match:
                    self.exclusiveWith = match.group(1).strip()
                    processed = True

            if not processed:
                print(f"Unhandled note: {n}. in unit {self.name}. Please check the format.")

    def finalize_regiment_options(self, keywords=[], unit_names=[], titled_units={}, subhero_categories=[]):
        for opt in self.regiment_option_lines:
            ro = RegimentOption(opt.strip(),
                                keywords=keywords,
                                unit_names=unit_names,
                                titled_units=titled_units,
                                subhero_categories=subhero_categories)
            if not ro.valid():
                print(f"Invalid regiment option: {ro.to_dict()}: {ro.line}")
            else:
                self.regiment_options.append(ro)

    def to_dict(self):
        return {
            "name": self.name,
            "unit_size": self.unit_size,
            "points": self.points,
            "keywords": self.keywords,
            "notes": self.notes,
            "base_size": self.base_size,
            "reinforceable": self.reinforceable,
            "subhero_categories": self.subhero_categories,
            "regiment_options": [ro.to_dict() for ro in self.regiment_options if ro.valid()],
            "requiredLeader": self.requiredLeader,
            "undersizeCondition": self.undersizeCondition,
            "retiringOn": self.retiringOn,
            "exclusiveWith": self.exclusiveWith,
            "legends": self.legends
        }

class FactionBattleProfiles:
    def __init__(self, name):
        self.faction_name = normalize_text(name.replace('\n', ' ').strip())
        self.battle_profiles = {} # unit name to UnitBattleProfile mapping
        self.other = {}
    
    def process_table(self, table):
        """Process a table to extract battle profile data."""
        table_type = determine_table_type(table)
        print(f"Processing table type: {table_type} for faction {self.faction_name}")
        if table_type == "heroes" or table_type == "units":
            self.process_units(table)
        if table_type == "legends_units" or table_type == "legends_heroes":
            self.process_units(table[1:], True)  # Skip the header row
        elif table_type == "other":
            self.process_other(table)
        pass

    def process_units(self, table, is_legends=False):
        """Process a row to extract unit battle profile data."""
        header = table[0]
        for row in table[1:]:
            unit_name = row[0]
            if not unit_name:
                continue

            unit_name = normalize_text(unit_name.replace('\n', ' ').strip())

            if unit_name not in self.battle_profiles:
                self.battle_profiles[unit_name] = UnitBattleProfile(unit_name)
            self.battle_profiles[unit_name].process_row(header, row)
            if is_legends:
                self.battle_profiles[unit_name].legends = True

    def process_other(self, table):
        """Process a table of other types."""
        header = table[0]
        for row in table[1:]:
            name = normalize_text(row[1].replace('\n', ' ').strip()) # name is the second column
            if name not in self.other:
                self.other[name] = OtherBattleProfile(name)
            self.other[name].process_row(header, row)

    def to_dict(self):
        profiles = [profile.to_dict() for profile in self.battle_profiles.values()]
        # Filter out profiles with no points or size and log warning for each filtered out profile
        for profile in profiles:
            if profile['unit_size'] in (None, "0", 0):
                print(f"Warning: Battle profile '{profile['name']}' has no size. It will be excluded from the output.")
        profiles = [profile for profile in profiles if profile['unit_size'] not in (None, "0", 0)]


        return {
            "name": self.faction_name,
            "battle_profiles": [profile.to_dict() for profile in self.battle_profiles.values()],
            "other": [profile.to_dict() for profile in self.other.values() if profile.points not in (None, "0", 0)]
        }

class RegimentOfRenown():
    def __init__(self, row):
        self.name = normalize_text(row[0].replace('\n', ' ').strip())
        unitSummaryLines = row[1].replace('\n', ' ').strip().split("•")
        self.points = int(row[2].strip()) if len(row) > 2 and row[2].strip().isdigit() else 0
        notes = row[3].strip() if len(row) > 3 else ""

        self.units = {} # unit name to count
        # the count is the number of times the unit appears not the number in front of the unit
        for line in unitSummaryLines:
            line = normalize_text(line).strip()
            if not line:
                continue
            # regex get part after number (optional)
            # 1 Gatebreaker Mega-Gargant becomes "Gatebreaker Mega-Gargant"
            parts = re.split(r"\d+", line, maxsplit=1)
            if len(parts) > 1:
                unit_name = parts[1].strip()
            else:
                unit_name = parts[0].strip()

            if unit_name not in self.units:
                self.units[unit_name] = 0
            self.units[unit_name] += 1

        self.allowedArmies = []
        notes = notes.split(":")[1]
        parts = notes.split(",")
        for part in parts:
            part = part.strip()
            if part:
                self.allowedArmies.append(part)

    def to_dict(self):
        return {
            "name": self.name,
            "units": self.units,
            "points": self.points,
            "allowedArmies": self.allowedArmies
        }

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
            points = row[1].strip() if len(row) > 1 else 0
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
            points = row[1].strip() if len(row) > 1 else 0
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

        keywords = list(set(keywords))  # Remove duplicates
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

def determine_table_type(table):
    """Determine the type of table based on its content."""
    if not table:
        return "unknown"

    # Compare header row
    header = table[0]
    header2 = table[1] if len(table) > 1 else []
    # heroes: HEROES UNIT SIZE POINTS REGIMENT OPTIONS NOTES BASE SIZE
    def header_includes(required):
        return all(col in header for col in required)

    if header_includes(["HEROES", "UNIT SIZE", "POINTS", "REGIMENT OPTIONS", "NOTES", "BASE SIZE"]):
        return "heroes"
    elif header_includes(["UNITS", "UNIT SIZE", "POINTS", "RELEVANT KEYWORDS", "NOTES", "BASE SIZE"]):
        return "units"
    elif header_includes(["TYPE", "NAME", "POINTS", "NOTES"]):
        return "other"
    elif header_includes(["NAME", "POINTS", "NOTES"]):
        return "universal_manifestations"
    elif "UNIT SUMMARY" in header:
        return "regiment_of_renown"
    elif "LEGENDS UNITS" in header2 or "LEGENDS UNITS" in header:
        return "legends_units"
    elif "LEGENDS HEROES" in header2 or "LEGENDS HEROES" in header:
        return "legends_heroes"
    else:
        return "unknown"

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

def extract_battle_profile_data(pdf):
    extractor = BPExtractor()
    for page in pdf.pages:
        extractor.process_page(page)
    extractor.finalize()
    return extractor.get_battle_profiles()