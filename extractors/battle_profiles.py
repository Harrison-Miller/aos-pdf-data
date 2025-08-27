import re
from extractors.utils import normalize_text, extract_points
from extractors.bp_table import determine_table_type
from extractors.regiment_option import RegimentOption

class OtherBattleProfile:
    def __init__(self, name):
        self.name = normalize_text(name.replace('\n', ' ').strip())
        self.type = None
        self.points = None
        self.notes = None

    def process_row(self, header, row):
        """Process a row to extract other battle profile data."""
        if "TYPE" in header:
            self.type = normalize_text(row[header.index("TYPE")].replace('\n', ' ').strip())
        if "POINTS" in header:
            self.points = extract_points(row[header.index("POINTS")])
        if "NOTES" in header:
            self.notes = normalize_text(row[header.index("NOTES")].replace('\n', ' ').strip())

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
        self.regiment_option_lines = []
        self.regiment_options = []
        self.notes = []
        self.base_size = None
        self.subhero_categories = []  # Initialize subhero categories
        self.reinforceable = False
        self.requiredLeader = ""
        self.undersizeCondition = ""
        self.retiringOn = ""
        self.exclusiveWith = ""
        self.legends = False
        self.hero = False

    def process_row(self, header, row):
        """Process a row to extract unit battle profile data."""
        if "UNIT SIZE" in header and row[header.index("UNIT SIZE")]:
            self.unit_size = row[header.index("UNIT SIZE")]
            self.reinforceable = self.unit_size != "1"
        if "POINTS" in header and row[header.index("POINTS")]:
            self.points = extract_points(row[header.index("POINTS")])
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
                self.reinforceable = True
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
            "legends": self.legends,
            "hero": self.hero
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

            isHero = "hero" in header[0].lower()
            self.battle_profiles[unit_name].hero = isHero

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
            "battle_profiles": profiles,
            "other": [profile.to_dict() for profile in self.other.values()]
        }