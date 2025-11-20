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

MEDICAL_TERMS = [
    " USP ", " FDA ", " DEA ", " CDC ", " NIH ", " HIPAA ",
    " NDC ", " CMS ", " CLIA ", " EMR ", " EHR ", " HCP ", " MSL ",
    " RA ", " PK ", " PD ", " IRB ", " PI ", " API ",
    " Medicare ", " Medicaid ", " VA ", " DoD ",
    " HEOR ", " ICER ", " QALY ", " MTM ",
    " Oncology ", " Cardiology ", " Neurology ", " Pharmacology ",
]

FILLER_PATTERNS = [
    r"\bum\b", r"\buh\b", r"\ber\b",
    r"\bumm+\b", r"\buhh+\b",
    r"\byou know\b",
    r"\bi mean\b",
    r"\bkind of\b",
    r"\bsort of\b",
    r"\bso\b",
    r"\bokay\b",
    r"\bbasically\b",
    r"\bactually\b",
    r"\bliterally\b",
]

NUM_WORDS = {
    "1": "one", "2": "two", "3": "three", "4": "four",
    "5": "five", "6": "six", "7": "seven", "8": "eight", "9": "nine"
}

# ==========================
#  CLEANING HELPERS
# ==========================

def remove_filler_words(text):
    for pat in FILLER_PATTERNS:
        text = re.sub(rf"[, ]*\b{pat}\b[, ]*", " ", text, flags=re.IGNORECASE)
    return text

def collapse_repeated_words(text):
    return re.sub(r"\b(\w+)\s+\1\b", r"\1", text, flags=re.IGNORECASE)

def convert_single_digits(text):
    return re.sub(r"\b([1-9])\b",
                  lambda m: NUM_WORDS[m.group(1)],
                  text)

def lowercase_common_words(text):
    def fix(match):
        word = match.group(0)
        if word.lower() in COMMON_LOWER_WORDS:
            return word.lower()
        return word
    return re.sub(r"\b[A-Z][a-z]+\b", fix, text)

def restore_medical_terms(text):
    for term in MEDICAL_TERMS:
        text = re.sub(term, term, text, flags=re.IGNORECASE)
    return text

def clean_text_block(text):
    text = remove_filler_words(text)
    text = collapse_repeated_words(text)
    text = convert_single_digits(text)
    text = lowercase_common_words(text)
    text = restore_medical_terms(text)
    return text.strip()

# ==========================
#  FIX CONJUNCTION COMMA RULE
# ==========================

def fix_conjunction_across_lines(lines):
    new = []
    for i, line in enumerate(lines):
        if i > 0 and "<v" in line:
            prev = new[-1].rstrip()
            text_only = line.split(">", 1)[1].lstrip()

            first_word = text_only.split(" ")[0].lower()

            if first_word in CONJUNCTIONS:
                if prev and prev[-1] not in ".?!,":
                    new[-1] = prev + ","
                line = line.replace(f"{first_word},", first_word, 1)

        new.append(line)
    return new

# ==========================
#  MAIN WEB-FRIENDLY CLEANER
# ==========================

def clean_vtt_text(vtt_text):
    lines = vtt_text.split("\n")
    cleaned = []

    for line in lines:
        if "<v" in line and ">" in line:
            tag, text = line.split(">", 1)
            cleaned_text = clean_text_block(text)
            line = f"{tag}>{cleaned_text}"

        cleaned.append(line)

    cleaned = fix_conjunction_across_lines(cleaned)

    retur
