from pdfplumber import PDF

class OtherBattleProfile:
    def __init__(self, name):
        self.name = name
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

class UnitBattleProfile:
    def __init__(self, name):
        self.name = name
        self.unit_size = None
        self.points = None
        self.keywords = []
        self.regiment_options = []
        self.notes = []
        self.base_size = None

    def process_row(self, header, row):
        """Process a row to extract unit battle profile data."""
        print(f"Processing row for unit: {self.name}: {header}: {row}")
        if "UNIT SIZE" in header:
            self.unit_size = row[header.index("UNIT SIZE")]
        if "POINTS" in header:
            self.points = row[header.index("POINTS")]
        if "RELEVANT KEYWORDS" in header:
            self.keywords = row[header.index("RELEVANT KEYWORDS")].split(",")
            self.keywords = [kw.strip() for kw in self.keywords if kw.strip()]
        if "REGIMENT OPTIONS" in header:
            self.regiment_options = row[header.index("REGIMENT OPTIONS")].split(",")
            self.regiment_options = [opt.strip() for opt in self.regiment_options if opt.strip()]
        if "NOTES" in header:
            self.notes = row[header.index("NOTES")].split(".")
            self.notes = [note.strip() for note in self.notes if note.strip()]
        if "BASE SIZE" in header:
            self.base_size = row[header.index("BASE SIZE")]

    def to_dict(self):
        return {
            "name": self.name,
            "unit_size": self.unit_size,
            "points": self.points,
            "keywords": self.keywords,
            "regiment_options": self.regiment_options,
            "notes": self.notes,
            "base_size": self.base_size
        }

class FactionBattleProfiles:
    def __init__(self, name):
        self.faction_name = name
        self.battle_profiles = {} # unit name to UnitBattleProfile mapping
        self.other = {}
    
    def process_table(self, table):
        """Process a table to extract battle profile data."""
        table_type = determine_table_type(table)
        print(f"Processing table type: {table_type} for faction {self.faction_name}")
        if table_type == "heroes" or table_type == "units":
            self.process_units(table)
        elif table_type == "other":
            self.process_other(table)
        pass

    def process_units(self, table):
        """Process a row to extract unit battle profile data."""
        header = table[0]
        for row in table[1:]:
            unit_name = row[0]
            if not unit_name:
                continue

            if unit_name not in self.battle_profiles:
                self.battle_profiles[unit_name] = UnitBattleProfile(unit_name)
            self.battle_profiles[unit_name].process_row(header, row)

    def process_other(self, table):
        """Process a table of other types."""
        print(f"Processing other table for faction {self.faction_name}")
        header = table[0]
        for row in table[1:]:
            name = row[1] # name is the second column
            if name not in self.other:
                self.other[name] = OtherBattleProfile(name)
            self.other[name].process_row(header, row)

    def to_dict(self):
        return {
            "name": self.faction_name,
            "battle_profiles": [profile.to_dict() for profile in self.battle_profiles.values()],
            "other": [profile.to_dict() for profile in self.other.values()]
        }

class BPExtractor:
    def __init__(self):
        self.factions = {} # name to FactionBattleProfiles mapping

    def process_page(self, page):
        
        # Extract text and tables from the page
        outside_text, tables = extract_bp_tables(page)
        title = outside_text[3]

        # Process each table to extract battle profile data
        for table in tables:
            table_type = determine_table_type(table)
            # TODO: handle universal manifestations separately
            if table_type != "unknown":
                if title not in self.factions:
                    self.factions[title] = FactionBattleProfiles(title)
                self.factions[title].process_table(table)

    def finalize(self):
        """Finalize the extraction process."""
        # This method can be used to perform any final processing or cleanup
        # For now, we just pass as we are collecting data in the process_page method
        pass

    def get_battle_profiles(self):
        """Get the extracted battle profiles."""
        return {
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
    elif "LEGENDS UNITS" in header:
        return "legends_units"
    elif "LEGENDS HEROES" in header:
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