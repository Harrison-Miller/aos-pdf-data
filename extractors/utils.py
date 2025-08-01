import unicodedata

def normalize_text(text):
    # Replace common problematic unicode characters
    replacements = {
        "\ufffd": ".",
        "“": '"',
        "”": '"',
        "‘": "'",
        "’": "'",
        "–": "-",
        "—": "-",
        "…": "...",
    }
    for k, v in replacements.items():
        text = text.replace(k, v)
    # Normalize to NFKD and encode to ASCII, ignoring errors
    text = unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode("ascii")
    return text