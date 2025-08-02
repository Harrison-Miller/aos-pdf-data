import unicodedata

def normalize_text(text):
    # Replace common problematic unicode characters
    replacements = {
        "\ufffd": ".",
        "“": '"',
        "”": '"',
        "‘": "'",
        "’": "'",
        "-": "-",
        "✹": "",
        "á": "a",
    # emdash to dash
        "—": "-",
        "‑": "-",
        "-": "-",
        "…": "...",
        "\u00d7": "x",
        "’": "'",
        "‑": "-",
    }
    ntext = text
    for k, v in replacements.items():
        ntext = ntext.replace(k, v)
    # Normalize to NFKD and encode to ASCII, ignoring errors
    # Instead of "ignore", you can use "replace" to show a replacement character (usually '?')
    ntext = unicodedata.normalize("NFKD", ntext).encode("ascii", "ignore").decode("ascii")
    if "?" in ntext:
        print(f"Warning: Some characters were replaced with '?' in: {text}")
    return ntext