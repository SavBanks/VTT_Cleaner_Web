import re

# ==========================
#  CONFIGURATION LISTS
# ==========================

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

# Medical terms / acronyms that stay exactly as typed
MEDICAL_TERMS = [
    " USP ", " FDA ", " DEA ", " CDC ", " NIH ", " HIPAA ",
    " NDC ", " CMS ", " CLIA ", " EMR ", " EHR ", " HCP ", " MSL ",
    " RA ", " PK ", " PD ", " IRB ", " PI ", " API ",
    " Medicare ", " Medicaid ", " VA ", " DoD ",
    " HEOR ", "ICER", "QALY", "MTM"
]

# Filler words (with comma cleanup)
FILLER_PATTERNS = [
    r"\bum\b", r"\buh\b", r"\ber\b",
    r"\bumm+\b", r"\buhh+\b",
    r"\byou know\b",
    r"\bi mean\b",
    r"\bkind of\b",
    r"\bsort of\b",
    r"\blike\b",
    r"\bso\b",
    r"\bwell\b",
    r"\bokay\b",
    r"\bbasically\b",
    r"\bactually\b",
    r"\bliterally\b"
]

NUM_WORDS = {
    "1": "one","2":"two","3":"three","4":"four",
    "5":"five","6":"six","7":"seven","8":"eight","9":"nine"
}

# ==========================
#   CLEANING FUNCTIONS
# ==========================

def remove_filler_words(text):
    for pat in FILLER_PATTERNS:
        text = re.sub(rf"[, ]*\b{pat}\b[, ]*", " ", text, flags=re.IGNORECASE)
    return text


def collapse_repeated_words_across_lines(text):
    return re.sub(r"\b(\w+)\s+\1\b", r"\1", text, flags=re.IGNORECASE)


def convert_single_digits(text):
    return re.sub(r"\b([1-9])\b",
        lambda m: NUM_WORDS[m.group(1)], text)


def lowercase_common_words(text):
    def fix(match):
        word = match.group(0)
        if word.lower() in COMMON_LOWER_WORDS:
            return word.lower()
        return word
    return re.sub(r"\b[A-Z][a-z]+\b", fix, text)


def restore_medical_terms(text):
    for term in MEDICAL_TERMS:
        clean_term = term.strip()
        text = re.sub(clean_term, clean_term, text, flags=re.IGNORECASE)
    return text


# -----------------------------------------
#  NEW FUNCTION: CAPITALIZE AFTER PUNCTUATION
# -----------------------------------------
def capitalize_after_punctuation(lines):
    new_lines = []

    for i, line in enumerate(lines):
        if i > 0 and "<v" in line:
            prev_line = new_lines[-1].rstrip()

            if prev_line.endswith((".", "?", "!")):
                parts = line.split(">", 1)
                if len(parts) == 2:
                    tag, text = parts
                    text = text.lstrip()
                    if text:
                        text = text[0].upper() + text[1:]
                    line = tag + ">" + text

        new_lines.append(line)

    return new_lines


# -----------------------------------------
# Conjunction fixes across lines
# -----------------------------------------
def fix_conjunction_across_lines(lines):
    new_lines = []

    for i, line in enumerate(lines):
        if i > 0:
            prev = new_lines[-1].rstrip()
            first_word = line.strip().split(" ")[0].lower()

            if first_word in CONJUNCTIONS:
                if prev and prev[-1] not in ".?!,":
                    new_lines[-1] = prev + ","

                line = re.sub(rf"^({first_word}),\s*",
                              rf"\1 ",
                              line,
                              flags=re.IGNORECASE)

        new_lines.append(line)

    return new_lines


# ==========================
#  MAIN CLEANING FUNCTION
# ==========================

def clean_vtt_file(input_path, output_path):

    with open(input_path, "r", encoding="utf-8") as f:
        lines = f.readlines()

    cleaned_lines = []

    for line in lines:

        if "<v" in line:
            tag, text = line.split(">", 1)
            text = remove_filler_words(text)
            text = collapse_repeated_words_across_lines(text)
            text = convert_single_digits(text)
            text = lowercase_common_words(text)
            text = restore_medical_terms(text)
            line = tag + ">" + text

        cleaned_lines.append(line)

    # Fix capitalization first
    cleaned_lines = capitalize_after_punctuation(cleaned_lines)

    # Fix conjunction placement
    cleaned_lines = fix_conjunction_across_lines(cleaned_lines)

    with open(output_path, "w", encoding="utf-8") as f:
        f.writelines(cleaned_lines)

    print(f"\n✔ Cleaning complete.\nSaved → {output_path}\n")
