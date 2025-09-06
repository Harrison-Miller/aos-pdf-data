import re
from datetime import datetime
import unicodedata
from extractors.utils import normalize_text

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
        self.finalize_question()
        self.finalize_rule()  # Finalize any previous rule
        self.finalize_section()  # Finalize any previous section
        # print(f"Starting section: {title}")
        self.section_title = title
        self.rules = []
        self.rule_title = None
        self.questions = []
        self.section_questions = []

    def finalize_section(self):
        if self.section_title or self.rules or self.section_questions:
            # print(f"Finalizing section: {self.section_title}")
            self.sections.append({
                "title": self.section_title or "Unknown Section",
                "questions": self.section_questions,
                "rules": self.rules
            })

            print(f"Finalized section: {self.section_title} with {len(self.section_questions)} questions and {len(self.rules)} rules.")
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
        for line in reversed(lines[:index]):
            text = line.strip()
            if not text or text == "NEW" or text == "UPDATED":
                break
            if text.isupper():
                rule_lines.insert(0, text)
            else:
                break
        if rule_lines:
            rule_title = " ".join(rule_lines)
        return rule_title

    def start_rule(self, title):
        """Start a new rule with the given title."""
        # If a rule is already started, save it
        self.finalize_rule()
        self.rule_title = title

    def finalize_rule(self):
        """Finalize the current rule and add it to the list."""
        self.finalize_question()
        if self.questions and (not self.rule_title or self.rule_title in ["Unknown Rule", "NEW", "UPDATED"]):
            # print(f"Finalizing questions for section: {self.section_title}")
            self.rule_title = title
            self.section_questions = self.questions
        if self.questions and self.rule_title:
            # print(f"Finalizing rule: {self.rule_title}")
            self.rules.append({
                "title": self.rule_title,
                "questions": self.questions
            })
        self.rule_title = None
        self.questions = []

    def start_question(self, first_line):
        """Start a new question."""
        # print(f"Starting question: {first_line}")
        self.collecting_question = True
        self.question_lines = [re.sub(r"^Q[:.]\s*", "", first_line)]

    def start_answer(self, first_line):
        """Start a new answer."""
        if self.collecting_answer:
            assert False, f"Answer already collecting when found: {first_line}, Q: {self.question_lines}, A: {self.answer_lines}"
        # print(f"Starting answer: {first_line}")
        self.collecting_answer = True
        self.answer_lines = [re.sub(r"^A[:.]\s*", "", first_line)]

    def finalize_question(self):
        """Finalize the current question and add it to the list."""
        if self.question_lines and self.answer_lines:
            question_text = normalize_text(" ".join(self.question_lines).strip())
            answer_text = normalize_text(" ".join(self.answer_lines).strip())
            if question_text and answer_text:
                if self.rule_title:
                    # print(f"Finalizing question: {question_text} with answer: {answer_text}")
                    self.questions.append({
                        "question": question_text,
                        "answer": answer_text,
                        # "updatedOn": datetime.now().strftime("%Y-%m-%d")
                    })
                else:
                    # print(f"Finalizing question without rule title: {question_text} with answer: {answer_text}")
                    self.section_questions.append({
                        "question": question_text,
                        "answer": answer_text,
                        # "updatedOn": datetime.now().strftime("%Y-%m-%d")
                    })
        self.collecting_question = False
        self.question_lines = []
        self.answer_lines = []
        self.collecting_answer = False

    def finalize(self):
        self.finalize_question()
        self.finalize_rule()
        
        # """Finalize the extraction by saving the last rule and section."""
        # if self.questions and self.rule_title:
        #     self.rules.append({
        #         "title": self.rule_title,
        #         "questions": self.questions
        #     })
        self.finalize_section()

        # remove any rules that start with DELETED
        for section in self.sections:
            section["rules"] = [rule for rule in section["rules"] if not rule["title"].startswith("DELETED")]
            # for rule in section["rules"]:
            #     if rule["title"].startswith("DELETED"):
            #         print(f"Removing deleted rule: {rule['title']} from section: {section['title']}")

    def extract_from_page(self, lines):
        """Process all lines from a single page."""
        for i, line in enumerate(lines):
            next_line = lines[i + 1] if i + 1 < len(lines) else None
            self.process_line(line, next_line)

    def get_sections(self):
        """Return the extracted sections."""
        return self.sections


def extract_text_from_columns(page):
    """Extract text from a two-column layout using vertical lines as boundaries."""
    words = page.extract_words()
    lines = page.lines
    outside_text = []
    column_text = []
    page_width = page.width
    page_height = page.height

    # Find vertical lines and construct bounding boxes
    vertical_lines = [line for line in lines if abs(line["x1"] - line["x0"]) < 5 and abs(line["y1"] - line["y0"]) > 50]
    valid_boxes = []
    buffer = 10  # pixels to add above/below line
    for index, vline in enumerate(vertical_lines):
        top = vline["top"] - buffer
        bottom = vline["bottom"] + buffer
        bbox = (0, top, page_width, bottom)
        try:
            cropped_page = page.crop(bbox)
            cropped_words = cropped_page.extract_words()
            image_text = " ".join(word["text"] for word in cropped_words)
            if contains_faq(image_text):
                area = (bbox[2] - bbox[0]) * (bbox[3] - bbox[1])
                valid_boxes.append((area, bbox, cropped_words))
            #     im = page.to_image()
            #     im.draw_rects([{"x0": bbox[0], "top": bbox[1], "x1": bbox[2], "bottom": bbox[3]}])
            #     im.draw_rects(cropped_words)
            #     im.draw_lines([vline])
            #     im.save(f"debug_cropped_line_{index}.png")
            # else:
            #     im = page.to_image()
            #     im.draw_rects([{"x0": bbox[0], "top": bbox[1], "x1": bbox[2], "bottom": bbox[3]}])
            #     im.draw_rects(cropped_words)
            #     im.draw_lines([vline])
            #     im.save(f"debug_invalid_line_{index}.png")
        except Exception:
            continue

    if valid_boxes:
        # Select the largest valid box by area
        _, largest_bbox, largest_words = max(valid_boxes, key=lambda x: x[0])
        image_bbox = {
            "top": largest_bbox[1],
            "bottom": largest_bbox[3],
            "left": largest_bbox[0],
            "right": largest_bbox[2]
        }
        # im = page.to_image()
        # im.draw_rects([{"x0": largest_bbox[0], "top": largest_bbox[1], "x1": largest_bbox[2], "bottom": largest_bbox[3]}])
        # im.save("debug_largest_line_bbox.png")
    else:
        # Fallback: use the whole page if no valid lines
        image_bbox = {"top": 0, "bottom": float("inf"), "left": 0, "right": float("inf")}

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
            lines.append(normalize_text(" ".join(current_line)))

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

def extract_faq_data(pdf_pages):
    """Extract FAQ data from a PDF with two-column layout."""
    extractor = FAQExtractor()

    try:
        for page in pdf_pages:
            extractor.process_page(page)
    except Exception as e:
        print(f"Unexpected error during extraction: {e}")
    finally:
        # Ensure finalize is always called
        extractor.finalize()

    sections = extractor.get_sections()
    print(f"Extracted {len(sections)} sections from FAQ.")
    return sections
