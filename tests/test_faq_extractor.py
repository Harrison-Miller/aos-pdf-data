import pdfplumber
from io import StringIO
from extractors.faq_extractor import extract_faq_data_from_lines

def test_extract_faq_data():
    # Mock PDF content
    text = """CORE RULES
RULES UPDATES
FREQUENTLY ASKED QUESTIONS
In this series of questions and answers, the rules-writing team respond to players’ queries and explain how the rules are intended to be used.
NEW
2.2 DICE
Q: If an ability allows me to re-roll one dice from an XD6 roll (e.g.
the Blades of the Hollow King ‘Aurelias’ ability), could I then use a
different ability to re-roll the entire XD6 roll?
A: No.
4.0 WARSCROLLS
Q: How should I resolve an ability that refers to an enemy’s Control
characteristic (e.g. Ushoran’s ‘Shroudcage Fragment’) if the target
does not have a Control characteristic (e.g. a manifestation)?
A: The target is treated as having a Control characteristic of 0.
5.0 ABILITIES
Q: Some abilities (e.g. ‘All-out Attack’) have a red timing bar. Can
these abilities only be used in the combat phase?
A: No. The words in the timing bar or, in the case of reactions
and passive abilities, the specific wording of the ability will let
you know exactly when you can use it; the colour is just there
as a play aid. If a phase is not specified, the colour indicates the
most common phase it is used in or, if it is used in multiple phases
equally, the timing bar is black.
Q: Some abilities have a green timing bar. What does this mean?
A: The green timing bar is used to indicate defensive abilities,
many of which can be used in multiple phases.
Q: Are non-passive abilities such as ‘Burning Wyrdflame’ optional
to use?
A: Yes. You must apply the effects of passive abilities and abilities
that state that they must be used if it is possible to do so, but all
other abilities are optional to use.
5.1 KEY WORDS
Q: In ‘Pick a friendly non-Hero Legion of the First Prince
Daemon Infantry or Cavalry unit that has been destroyed to
be the target’ (and similar wordings with multiple keywords), does
‘Cavalry unit’ mean just that (i.e. with no other keywords) or
does it mean ‘ friendly non-Hero Legion of the First Prince
Daemon Cavalry unit’?
A: It means ‘friendly non-Hero Legion of the First Prince
Daemon Cavalry unit’."""

    # Run the extractor
    result = extract_faq_data_from_lines(text.splitlines())

    # Assert the structure of the result
    assert len(result) == 1
    assert result[0]["title"] == "CORE RULES"

    print("Extracted FAQ Data:" + str(result))

    expected_questions = [
        "If an ability allows me to re-roll one dice from an XD6 roll (e.g. the Blades of the Hollow King ‘Aurelias’ ability), could I then use a different ability to re-roll the entire XD6 roll?",
        "How should I resolve an ability that refers to an enemy’s Control characteristic (e.g. Ushoran’s ‘Shroudcage Fragment’) if the target does not have a Control characteristic (e.g. a manifestation)?",
        "Some abilities (e.g. ‘All-out Attack’) have a red timing bar. Can these abilities only be used in the combat phase?",
        "Some abilities have a green timing bar. What does this mean?",
        "Are non-passive abilities such as ‘Burning Wyrdflame’ optional to use?",
        "In ‘Pick a friendly non-Hero Legion of the First Prince Daemon Infantry or Cavalry unit that has been destroyed to be the target’ (and similar wordings with multiple keywords), does ‘Cavalry unit’ mean just that (i.e. with no other keywords) or does it mean ‘ friendly non-Hero Legion of the First Prince Daemon Cavalry unit’?"
    ]

    actual_questions = [q["question"] for rule in result[0]["rules"] for q in rule["questions"]]
    for expected_q in expected_questions:
        assert expected_q in actual_questions

    # Print the result for manual verification
    print(result)

if __name__ == "__main__":
    test_extract_faq_data()
