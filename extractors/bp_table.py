
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