
from extractors.utils import normalize_text, extract_points
import re

class RegimentOfRenown():
    def __init__(self, row):
        self.name = normalize_text(row[0].replace('\n', ' ').strip())
        unitSummaryLines = row[1].replace('\n', ' ').strip().split("•")
        self.points = extract_points(row[2].strip())
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