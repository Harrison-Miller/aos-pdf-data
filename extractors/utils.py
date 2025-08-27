import unicodedata
import re

def normalize_text(text):
    # replace tags
    text = text.replace("NEW", "")
    text = text.replace("UPDATED", "")

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
        "\u2739": "",
        "’": "'",
        "‑": "-",
    }
    ntext = text
    for k, v in replacements.items():
        ntext = ntext.replace(k, v)
    # Normalize to NFKD and encode to ASCII, ignoring errors
    # Instead of "ignore", you can use "replace" to show a replacement character (usually '?')
    ntext = unicodedata.normalize("NFKD", ntext).encode("ascii", "ignore").decode("ascii")
    # if "?" in ntext:
    #     print(f"Warning: Some characters were replaced with '?' in: {text}")
    return ntext.strip()

def extract_points(text):
    # Always convert to an integer, return 0 if not possible
    try:
        # capture x (+|- y) we always want x
        match = re.match(r"[-+]?\d+", normalize_text(text))
        return int(match.group(0)) if match else 0
    except Exception:
        return 0