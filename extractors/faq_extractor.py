import re
from datetime import datetime


class FAQExtractor:
    def __init__(self):
        self.sections = []
        self.section_title = None
        self.rules = []
        self.rule_title = None
        self.questions = []
        self.section_questions = []
        self.collecting_question = False
        self.question_lines = []
        self.collecting_answer = False
        self.answer_lines = []
        self.all_rule_titles = set()  # Store all rule titles to avoid duplicates

    def process_page(self, page):
        """Process a single line of text."""
        left_lines, right_lines, outside_lines = extract_text_from_columns(page)
        print("outside_lines:", outside_lines)

        # If no FAQ pairs are found, skip processing
        if (not contains_faq(left_lines + right_lines)):
            return

        # Detect section title
        section_title = self.find_section_title(outside_lines)
        if section_title:
            self.start_section(section_title)
            
        faq_lines = left_lines + right_lines

        # find all rule titles first
        for i, line in enumerate(faq_lines):
            if line.startswith("Q:"):
                rule_title = self.find_rule_title(faq_lines, i)
                if rule_title:
                    self.all_rule_titles.add(rule_title)


        # Process FAQ Lines
        for i, line in enumerate(faq_lines):
            # If a rule any rule title from self.all_rule_titles is found, finalize the previous question
            if self.all_rule_titles and any(title.startswith(line) for title in self.all_rule_titles):
                # get appropriate rule title from all rule titles
                current_rule_title = next((title for title in self.all_rule_titles if title.startswith(line)), None)
                self.finalize_question()
                self.start_rule(current_rule_title)

            if line.startswith("Q:") or line.startswith("Q."):
                self.finalize_question()
                self.start_question(line)
            elif line.startswith("A:") or line.startswith("A."):
                self.start_answer(line)
            elif self.collecting_answer:
                self.answer_lines.append(line.strip())
            elif self.collecting_question:
                self.question_lines.append(line.strip())

    def find_section_title(self, lines):
        """Find the section title in the provided lines."""
        for line in lines:
            if "FREQUENTLY ASKED QUESTIONS" in line:
                return lines[3].strip() if len(lines) > 3 else "Unknown Section"
        return None

    def start_section(self, title):
        """Start a new section with the given title."""
        self.finalize_section()  # Finalize any previous section
        print(f"Starting section: {title}")
        self.section_title = title
        self.rules = []
        self.rule_title = None
        self.questions = []
        self.section_questions = []

    def finalize_section(self):
        if self.section_title or self.rules or self.section_questions:
            print(f"Finalizing section: {self.section_title}")
            self.sections.append({
                "title": self.section_title or "Unknown Section",
                "questions": self.section_questions,
                "rules": self.rules
            })
            self.section_title = None
            self.rules = []
            self.rule_title = None
            self.questions = []
            self.section_questions = []

    def find_rule_title(self, lines, index):
        """Find the rule title in the provided lines."""
        # collect every line before the index that isupper until empty or not upper
        rule_title = None
        rule_lines = []
        # Read lines going up (reverse) from index-1 to 0
        print("looking for rule title in lines before index:", index)
        for line in reversed(lines[:index]):
            text = line.strip()
            if not text or text == "NEW" or text == "UPDATED":
                print(f"done looking for rule title: {text}")
                break
            if text.isupper():
                print(f"Adding to rule title: {text}")
                rule_lines.insert(0, text)
            else:
                print(f"Stopping rule title collection at: {text}")
                break
        if rule_lines:
            rule_title = " ".join(rule_lines)
        return rule_title

    def start_rule(self, title):
        """Start a new rule with the given title."""
        # If a rule is already started, save it
        if self.questions and (not self.rule_title or self.rule_title in ["Unknown Rule", "NEW", "UPDATED"]):
            print(f"Finalizing questions for section: {self.section_title}")
            self.rule_title = title
            self.section_questions = self.questions
        if self.questions and self.rule_title:
            print(f"Finalizing rule: {self.rule_title}")
            self.rules.append({
                "title": self.rule_title,
                "questions": self.questions
            })
        print(f"Starting rule: {title}")
        self.rule_title = title
        self.questions = []

    def start_question(self, first_line):
        """Start a new question."""
        print(f"Starting question: {first_line}")
        self.collecting_question = True
        self.question_lines = [re.sub(r"^Q[:.]\s*", "", first_line)]

    def start_answer(self, first_line):
        """Start a new answer."""
        if self.collecting_answer:
            assert False, f"Answer already collecting when found: {first_line}, Q: {self.question_lines}, A: {self.answer_lines}"
        print(f"Starting answer: {first_line}")
        self.collecting_answer = True
        self.answer_lines = [re.sub(r"^A[:.]\s*", "", first_line)]

    def finalize_question(self):
        """Finalize the current question and add it to the list."""
        if self.question_lines and self.answer_lines:
            question_text = " ".join(self.question_lines).strip()
            answer_text = " ".join(self.answer_lines).strip()
            if question_text and answer_text:
                if self.rule_title:
                    print(f"Finalizing question: {question_text} with answer: {answer_text}")
                    self.questions.append({
                        "question": question_text,
                        "answer": answer_text,
                        "updatedOn": datetime.now().strftime("%Y-%m-%d")
                    })
                else:
                    print(f"Finalizing question without rule title: {question_text} with answer: {answer_text}")
                    self.section_questions.append({
                        "question": question_text,
                        "answer": answer_text,
                        "updatedOn": datetime.now().strftime("%Y-%m-%d")
                    })
        self.collecting_question = False
        self.question_lines = []
        self.answer_lines = []
        self.collecting_answer = False

    def finalize(self):
        self.finalize_question()
        
        """Finalize the extraction by saving the last rule and section."""
        if self.questions and self.rule_title:
            self.rules.append({
                "title": self.rule_title,
                "questions": self.questions
            })
        self.finalize_section()

    def extract_from_page(self, lines):
        """Process all lines from a single page."""
        for i, line in enumerate(lines):
            next_line = lines[i + 1] if i + 1 < len(lines) else None
            self.process_line(line, next_line)

    def get_sections(self):
        """Return the extracted sections."""
        return self.sections


def extract_text_from_columns(page):
    """Extract text from a two-column layout using images as boundaries."""
    words = page.extract_words()
    images = page.images
    outside_text = []
    column_text = []

    # Find valid images (by area) that contain at least one Q&A pair
    valid_images = []

    for image in images:
        try:
            # Try cropping the image region using page.crop
            try:
                cropped_page = page.crop((image["x0"], image["top"], image["x1"], image["bottom"]))
                cropped_words = cropped_page.extract_words()
                image_text = " ".join(word["text"] for word in cropped_words)
                # Check for Q&A pattern
                if contains_faq(image_text):
                    area = (image["x1"] - image["x0"]) * (image["bottom"] - image["top"])
                    valid_images.append((area, image))
            except Exception:
                continue
        except Exception:
            continue

    if valid_images:
        # Select the largest valid image by area
        _, largest_image = max(valid_images, key=lambda x: x[0])
        image_bbox = {
            "top": largest_image["top"],
            "bottom": largest_image["bottom"],
            "left": largest_image["x0"],
            "right": largest_image["x1"]
        }
    else:
        # Fallback: use the whole page if no valid images
        image_bbox = {"top": 0, "bottom": float("inf"), "left": 0, "right": float("inf")}

    print(f"Image bbox: {image_bbox} page size: {page.width}x{page.height}")

    # Separate words into outside text and column text
    for word in words:
        if word["top"] < image_bbox["top"] or word["bottom"] > image_bbox["bottom"]:
            outside_text.append(word)
        else:
            column_text.append(word)

    # Split column text into left and right columns based on the midpoint of the image
    midpoint = (image_bbox["left"] + image_bbox["right"]) / 2
    left_column = [word for word in column_text if word["x0"] < midpoint]
    right_column = [word for word in column_text if word["x0"] >= midpoint]

    # Sort words by their vertical position (top)
    outside_text.sort(key=lambda w: w["top"])
    left_column.sort(key=lambda w: w["top"])
    right_column.sort(key=lambda w: w["top"])

    # Combine words into lines
    def combine_words(column):
        lines = []
        current_line = []
        current_top = None

        for word in column:
            if current_top is None or abs(word["top"] - current_top) > 5:  # Adjust threshold as needed
                if current_line:
                    lines.append(" ".join(current_line))
                current_line = [word["text"]]
                current_top = word["top"]
            else:
                current_line.append(word["text"])

        if current_line:
            lines.append(" ".join(current_line))

        return lines

    outside_lines = combine_words(outside_text)
    left_lines = combine_words(left_column)
    right_lines = combine_words(right_column)

    # Return a tuple with left, right, and outside text
    return left_lines, right_lines, outside_lines

# checks if Q&A pairs are present in the text
def contains_faq(text):
    # if text is lines join them
    if isinstance(text, list):
        text = " ".join(text)
    return bool(re.search(r"Q:.*A:.*", text, re.DOTALL))

def extract_faq_data(pdf):
    """Extract FAQ data from a PDF with two-column layout."""
    extractor = FAQExtractor()

    try:
        for page in pdf.pages:
            extractor.process_page(page)
    except Exception as e:
        print(f"Unexpected error during extraction: {e}")
    finally:
        # Ensure finalize is always called
        extractor.finalize()

    sections = extractor.get_sections()
    print(f"Extracted {len(sections)} sections from FAQ.")
    return sections
