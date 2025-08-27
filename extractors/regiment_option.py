from extractors.utils import normalize_text
import re

class RegimentOption:
    def __init__(self, line, keywords=[], unit_names=[], titled_units={}, subhero_categories=[]):
        line = normalize_text(line.replace('\n', ' ').strip())
        self.line = line
        self.min = 0
        self.max = 0
        self.keywords = []
        self.nonKeywords = []
        self.subhero_categories = []
        self.unit_names = []

        if line == "None":
            line = ""
            return

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
            line = line.replace(" or ", " ")

        for part in parts:
            part = part.strip()
            # check subhero categories
            if any(cat.lower() == part.lower() for cat in subhero_categories):
                self.subhero_categories.append(part)
            # allow plural forms for subhero categories
            elif any(cat.lower() + "s" == part.lower() for cat in subhero_categories):
                # part without s
                self.subhero_categories.append(part[:-1] if part.endswith("s") else part)


            # check if we consume the whole keyword
            isCompoundKeyword = False
            # try non-keywords first
            # check lower
            if part.startswith("non-"):
                k = part[4:].strip()
                if any(k.lower() == kw.lower() for kw in keywords):
                    self.nonKeywords.append(k)

            testPart = part
            # try whole keyword match
            if any(kw.lower() == testPart.lower() for kw in keywords):
                self.keywords.append(testPart)
                testPart = ""
            else:
                # Check if any keyword exists in the full part (case-insensitive)
                nonKeywordsToAdd = []
                keywordsToAdd = []
                for kw in keywords:
                    if f'non-{kw.lower()}' in testPart.lower():
                        # Remove the keyword from the part (case-insensitive)
                        pattern = re.compile(re.escape(f'non-{kw}'), re.IGNORECASE)
                        testPart = pattern.sub("", testPart).strip()
                        nonKeywordsToAdd.append(kw)
                    if kw.lower() in testPart.lower():
                        # Remove the keyword from the part (case-insensitive)
                        pattern = re.compile(re.escape(kw), re.IGNORECASE)
                        testPart = pattern.sub("", testPart).strip()
                        keywordsToAdd.append(kw)

                if testPart == "":
                    # If the test part is empty, it means all keywords were consumed
                    self.keywords.extend(keywordsToAdd)
                    self.nonKeywords.extend(nonKeywordsToAdd)

            if testPart != "":
                # check unit names
                if any(name.lower() == part.lower() for name in unit_names):
                    self.unit_names.append(part)
                elif any(name.lower() == part.lower() for name in titled_units):
                    # Find the matching titled unit key and get its full name
                    for key in titled_units:
                        if key.lower() == part.lower():
                            full_name = titled_units[key]
                            self.unit_names.append(full_name)
                            break

        # test if we consumed everything
        # print(f"Testing line: {line}")
        testLine = line.lower()
        for kw in self.keywords:
            testLine = testLine.replace(kw.lower(), "").strip()
        for kw in self.nonKeywords:
            testLine = testLine.replace(f"non-{kw.lower()}", "").strip()
        for cat in self.subhero_categories:
            if cat.lower() + "s" in testLine:
                testLine = testLine.replace((cat.lower() + "s"), "").strip()
            testLine = testLine.replace(cat.lower(), "").strip()
        for name in self.unit_names:
            testLine = testLine.replace(name.lower(), "").strip()
            for title_name, full_name in titled_units.items():
                if name.lower() == full_name.lower():
                    testLine = testLine.replace(title_name.lower(), "").strip()

        if testLine != "":
            print(f"Warning: Unparsed part in regiment option '{line}': '{testLine}'")

    def valid(self):
        return self.line == "None" or ((self.max == -1 or self.max > 0) and (self.keywords or self.nonKeywords or self.subhero_categories or self.unit_names))

    def to_dict(self):
        return {
            "min": self.min,
            "max": self.max,
            "keywords": self.keywords,
            "nonKeywords": self.nonKeywords,
            "subhero_categories": self.subhero_categories,
            "unit_names": self.unit_names
        }

    
