import re

# ==========================
#  CONFIGURATION LISTS
# ==========================

CONJUNCTIONS = ["and", "but", "or", "nor", "yet", "so"]

COMMON_LOWER_WORDS = [
    "the", "and", "but", "or", "nor", "for", "yet", "so", "a", "an", "to", "in", "on",
    "at", "by", "from", "with", "of", "as", "that", "this", "these", "those", "is",
    "are", "was", "were", "be", "been", "being", "it", "its", "if", "then", "else",
    "also", "not", "very", "just", "such", "than", "because", "when", "where", "while",
    "however", "therefore", "thus", "although", "though", "unless", "until", "whether",
    "like", "unlike", "about", "above", "below", "under", "over", "again", "already",
    "still", "even", "too", "very", "maybe", "perhaps", "almost", "nearly", "basically",
    "actually", "literally", "really", "kind", "sort", "part", "might", "should",
    "could", "would", "will", "can", "may", "shall", "up", "down", "out", "into",
    "through", "across", "between", "among"
]

# Medical terms (must be uppercase exactly)
MEDICAL_TERMS = [
    "USP", "FDA", "DEA", "CDC", "NIH", "HIPAA",
    "NDC", "CMS", "CLIA", "EMR", "EHR", "HCP", "MSL",
    "RA", "PK", "PD", "IRB", "PI", "API",
    "Medicare", "Medicaid", "VA", "DoD",
    "HEOR", "ICER", "QALY", "MTM",
    "Oncology", "Cardiology", "Neurology", "Pharmacology"
]

FILLER_PATTERNS = [
    r"\bum\b", r"\buh\b", r"\ber\b", r"\bumm+\b", r"\buhh+\b",
    r"\byou know\b", r"\bi mean\b", r"\bkind of\b", r"\bsort of\b",
    r"\bso\b", r"\bokay\b", r"\bbasically\b", r"\bactually\b", r"\bliterally\b"
]

NUM_WORDS = {
    "1": "one", "2": "two", "3": "three", "4": "four",
    "5": "five", "6": "six", "7": "seven", "8": "eight", "9": "nine"
}

# ==========================
#   HELPERS
# ==========================

def remove_filler_words(text):
    for pat in FILLER_PATTERNS:
        text = re.sub(rf"[, ]*\b{pat}\b[, ]*", " ", text, flags=re.IGNORECASE)
    return text


def remove_unwanted_repeated_words(text):
    # Fix ONLY the “I, I” case (preserve comma)
    text = re.sub(r"\bI,\s*I\b", "I", text)
    return text


def convert_single_digits(text):
    # Skip times like 8:30
    return re.sub(
        r"\b([1-9])\b(?!:)",  # Not followed by a colon → avoids time conversion
        lambda m: NUM_WORDS[m.group(1)],
        text
    )


def lowercase_common_words(text):
    def fix(match):
        word = match.group(0)
        if word.lower() in COMMON_LOWER_WORDS:
            return word.lower()
        return word
    return re.sub(r"\b[A-Z][a-z]+\b", fix, text)


def restore_medical_terms(text):
    for term in MEDICAL_TERMS:
        text = re.sub(
            rf"\b{term}\b",
            term,
            text,
            flags=re.IGNORECASE
        )
    return text


def capitalize_first_word(text):
    stripped = text.lstrip()
    leading_spaces = len(text) - len(stripped)

    if not stripped:
        return text

    parts = stripped.split(" ", 1)
    first_word = parts[0]
    rest = parts[1] if len(parts) > 1 else ""

    # Capitalize only the first alphabetic character
    if first_word[0].isalpha():
        first_word = first_word[0].upper() + first_word[1:].lower()

    rebuilt = first_word + (" " + rest if rest else "")
    return " " * leading_spaces + rebuilt


def fix_conjunction_across_lines(lines):
    new = []
    for i, line in enumerate(lines):
        if i > 0:
            prev = new[-1].rstrip()
            word = line.strip().split(" ")[0].lower()

            if word in CONJUNCTIONS:
                if prev and prev[-1] not in ".?!,":
                    new[-1] = prev + ","
                line = re.sub(rf"^({word}),\s*", rf"\1 ", line, flags=re.IGNORECASE)

        new.append(line)
    return new


# ==========================
#  MAIN FUNCTION
# ==========================

def clean_vtt_text(input_path, output_path):
    with open(input_path, "r", encoding="utf-8") as f:
        lines = f.readlines()

    cleaned = []

    for line in lines:
        stripped = line.strip()

        # Skip untouched lines
        if stripped == "" or \
           stripped.startswith("WEBVTT") or \
           "-->" in stripped or \
           stripped.startswith("NOTE") or \
           stripped.startswith("{") or \
           stripped.startswith("}") or \
           stripped.startswith("RAW") or \
           not "<v" in line:
            cleaned.append(line)
            continue

        # Process speaker lines
        before, after = line.split(">", 1)
        text = after

        text = remove_filler_words(text)
        text = text.strip()

        text = remove_unwanted_repeated_words(text)
        text = convert_single_digits(text)
        text = lowercase_common_words(text)
        text = restore_medical_terms(text)
        text = capitalize_first_word(text)

        cleaned.append(before + ">" + text + "\n")

    cleaned = fix_conjunction_across_lines(cleaned)

    with open(output_path, "w", encoding="utf-8") as f:
        f.writelines(cleaned)

    print(f"\n✔ Cleaning complete.\nSaved → {output_path}\n")
