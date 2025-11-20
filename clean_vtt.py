import re

# ============================================================
# CONFIG LISTS
# ============================================================

CONJUNCTIONS = ["and", "but", "or", "nor", "yet", "so"]

COMMON_LOWER_WORDS = [
    "the","and","but","or","nor","for","yet","so","a","an","to","in","on","at","by",
    "from","with","of","as","that","this","these","those","is","are","was","were",
    "be","been","being","it","its","if","then","else","also","not","very","just",
    "such","than","because","when","where","while","however","therefore","thus",
    "although","though","unless","until","whether","like","unlike","about","above",
    "below","under","over","again","already","still","even","too","very","maybe",
    "perhaps","almost","nearly","basically","actually","literally","really",
    "kind","sort","part","might","should","could","would","will","can","may",
    "shall","up","down","out","into","through","across","between","among",
]

MEDICAL_TERMS = [
    " USP ", " FDA ", " DEA ", " CDC ", " NIH ", " HIPAA ",
    " NDC ", " CMS ", " CLIA ", " EMR ", " EHR ", " HCP ", " MSL ",
    " RA ", " PK ", " PD ", " IRB ", " PI ", " API ",
    " Medicare ", " Medicaid ", " VA ", " DoD ",
    " HEOR ", " ICER ", "QALY", " MTM ",
    " Oncology ", " Cardiology ", " Neurology ", " Pharmacology ",
]

FILLER_PATTERNS = [
    r"um", r"uh", r"er", r"umm+", r"uhh+",
    r"you know", r"i mean", r"kind of", r"sort of",
    r"okay", r"basically", r"actually", r"literally",
]

# Only fix THESE repeated words:  "I, I"
STRICT_REPEAT_WORDS = ["I"]

NUM_WORDS = {
    "1": "one", "2": "two", "3": "three", "4": "four",
    "5": "five", "6": "six", "7": "seven", "8": "eight", "9": "nine"
}

TIMESTAMP_PATTERN = re.compile(r"\d{1,2}:\d{2}")


# ============================================================
# HELPERS
# ============================================================

def remove_filler_words(text):
    for pat in FILLER_PATTERNS:
        text = re.sub(rf"(^|\s){pat}([, ]+|$)", " ", text, flags=re.IGNORECASE)
    return text


def collapse_repeated_specific(text):
    """
    Only collapse "I, I" → "I"
    Does NOT touch "that, that", "then, then", etc.
    """
    for w in STRICT_REPEAT_WORDS:
        pattern = rf"\b{w},\s*{w}\b"
        text = re.sub(pattern, w, text)
    return text


def convert_single_digits(text):
    """
    Convert single digits to words EXCEPT inside timestamps ("8:30").
    """
    parts = re.split(r'(\d+:\d+)', text)  # keep timestamps intact

    new_parts = []
    for part in parts:
        if TIMESTAMP_PATTERN.fullmatch(part):
            new_parts.append(part)
            continue

        converted = re.sub(r"\b([1-9])\b",
                           lambda m: NUM_WORDS[m.group(1)],
                           part)
        new_parts.append(converted)

    return "".join(new_parts)


def lowercase_common_words(text):
    def fix(m):
        word = m.group(0)
        if word.lower() in COMMON_LOWER_WORDS:
            return word.lower()
        return word
    return re.sub(r"\b[A-Z][a-z]+\b", fix, text)


def capitalize_after_filler_removal(text):
    """
    Capitalize the first alphabetic character of the line.
    Works even if filler removal created leading spaces.
    """
    i = 0
    while i < len(text) and not text[i].isalpha():
        i += 1

    if i < len(text) and text[i].islower():
        text = text[:i] + text[i].upper() + text[i+1:]

    return text


def restore_medical_terms(text):
    for term in MEDICAL_TERMS:
        cleaned = term.strip()
        text = re.sub(cleaned, cleaned, text, flags=re.IGNORECASE)
    return text


# ============================================================
# MAIN CLEAN FUNCTION
# ============================================================

def clean_vtt_text(input_path, output_path):
    with open(input_path, "r", encoding="utf-8") as f:
        lines = f.readlines()

    cleaned_lines = []

    for line in lines:
        stripped = line.strip()

        # DO NOT clean any of this:
        if (
            stripped == "" or
            stripped == "WEBVTT" or
            stripped.startswith("NOTE") or
            stripped.startswith("{") or
            "-->" in line or
            "<" in line and ">" in line and not line.startswith("<v")
        ):
            cleaned_lines.append(line)
            continue

        # Only clean real speaker lines like: <v Mark>text...
        if "<v" in line and ">" in line:
            prefix, text = line.split(">", 1)
            text = text.strip()

            original = text

            text = remove_filler_words(text)
text = text.strip()

text = collapse_repeated_specific(text)
text = convert_single_digits(text)
text = lowercase_common_words(text)
text = restore_medical_terms(text)

# MUST BE LAST
text = capitalize_after_filler_removal(text)

            cleaned_lines.append(prefix + ">" + text + "\n")
        else:
            cleaned_lines.append(line)

    # Preserve ALL original spacing automatically by writing exact list
    with open(output_path, "w", encoding="utf-8") as f:
        f.writelines(cleaned_lines)

    print(f"\n✔ Cleaning complete.\nSaved → {output_path}\n")
