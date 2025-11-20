import re

# ==========================
#  CONFIGURATION LISTS
# ==========================

# Conjunctions that should be preceded by a comma when continuing a sentence
CONJUNCTIONS = ["and", "but", "or", "nor", "yet", "so"]

# Large list of common words that should stay lowercase when mid-sentence
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

# Medical terms & acronyms that should remain capitalized EXACTLY as written
MEDICAL_TERMS = [
    " USP ", " FDA ", " DEA ", " CDC ", " NIH ", " HIPAA ",
    " NDC ", " CMS ", " CLIA ", " EMR ", " EHR ", " HCP ", " MSL ",
    " RA ", " PK ", " PD ", " IRB ", " PI ", " API ",
    " Medicare ", " Medicaid ", " VA ", " DoD ",
    " HEOR ", " ICER ", "QALY", " MTM ",
    " Oncology ", " Cardiology ", " Neurology ", " Pharmacology ",
]

# Filler words (with comma cleanup)
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
# Remove "right"

# Number word mapping
NUM_WORDS = {
    "1": "one", "2": "two", "3": "three", "4": "four",
    "5": "five", "6": "six", "7": "seven", "8": "eight", "9": "nine"
}

# ==========================
#   FUNCTIONS
# ==========================

def remove_filler_words(text):
    for pat in FILLER_PATTERNS:
        # remove filler word with optional commas/spaces
        text = re.sub(rf"[, ]*\b{pat}\b[, ]*", " ", text, flags=re.IGNORECASE)
    # collapse multiple spaces
    text = re.sub(r"\s{2,}", " ", text)
    return text.strip()

def collapse_repeated_words_across_lines(text):
    return re.sub(r"\b(\w+)\s+\1\b", r"\1", text, flags=re.IGNORECASE)

def convert_single_digits(text):
    return re.sub(
        r"\b([1-9])\b",
        lambda m: NUM_WORDS[m.group(1)],
        text
    )

def fix_conjunction_across_lines(lines):
    new_lines = []
    for i, line in enumerate(lines):
        if i > 0:
            prev = new_lines[-1].rstrip()
            # safe-get first word of this line (after tag if present)
            try:
                word = line.split(">", 1)[1].strip().split(" ")[0].lower()
            except IndexError:
                word = ""
            if word in CONJUNCTIONS:
                # If previous line ends *without* punctuation, add comma
                if prev and prev[-1] not in ".?!,":
                    new_lines[-1] = prev + ","
                # Remove stray comma after conjunction
                line = re.sub(rf"^({word}),\s*", rf"\1 ", line, flags=re.IGNORECASE)

        new_lines.append(line)
    return new_lines

def lowercase_common_words(text):
    def fix(match):
        word = match.group(0)
        lw = word.lower()
        if lw in COMMON_LOWER_WORDS:
            return lw
        return word
    return re.sub(r"\b[A-Z][a-z]+\b", fix, text)

def restore_medical_terms(text):
    for term in MEDICAL_TERMS:
        text = re.sub(term, term, text, flags=re.IGNORECASE)
    return text

# ----- NEW: collapse "I, I" pattern specifically (leave other comma-repeats alone) -----
def collapse_repeated_I_comma(text):
    # Replace "I, I" or "i, i" (possibly with spaces) with "I"
    return re.sub(r'\b[Ii]\s*,\s*[Ii]\b', 'I', text)

# ----- NEW: detect if original text started with a filler pattern -----
# compile a combined leading-filler regex for speed
_LEADING_FILLER_RE = re.compile(r'^\s*(?:' + r'|'.join(pat for pat in FILLER_PATTERNS) + r')', flags=re.IGNORECASE)

def original_starts_with_filler(orig_text):
    return bool(_LEADING_FILLER_RE.search(orig_text))

def capitalize_first_alpha(text):
    # find first alphabetical char and uppercase it
    m = re.search(r'[A-Za-z]', text)
    if not m:
        return text
    idx = m.start()
    return text[:idx] + text[idx].upper() + text[idx+1:]


# ==========================
#  MAIN CLEANING FUNCTION
# ==========================

def clean_vtt_text(input_path, output_path):
    """
    Clean the VTT file at input_path and save to output_path.
    Preserves timestamps and tags; only edits spoken text after the '>' in <v ...> lines.
    """
    with open(input_path, "r", encoding="utf-8") as f:
        lines = f.readlines()

    cleaned_lines = []

    for i, line in enumerate(lines):
        original_line = line

        # ONLY clean speaker text lines (those containing "<v" and a ">")
        if "<v" in line and ">" in line:
            # extract original spoken portion (everything after first '>')
            orig_text_part = line.split(">", 1)[1]

            # run the existing cleaning pipeline
            text_part = remove_filler_words(orig_text_part)
            text_part = collapse_repeated_words_across_lines(text_part)
            text_part = convert_single_digits(text_part)
            text_part = lowercase_common_words(text_part)
            text_part = restore_medical_terms(text_part)

            # NEW: collapse "I, I" comma-repeated pronoun specifically
            text_part = collapse_repeated_I_comma(text_part)

            # Determine whether to capitalize the first alphabetical char:
            #  - If the previous cleaned line ended with sentence punctuation (., ?, !)
            #  - OR if the original (pre-clean) text started with a filler (e.g. "Um, so ...")
            prev_ends_sentence = False
            if cleaned_lines:
                prev_line_text = cleaned_lines[-1].rstrip()
                if prev_line_text.endswith((".", "?", "!")):
                    prev_ends_sentence = True

            started_with_filler = original_starts_with_filler(orig_text_part)

            if prev_ends_sentence or started_with_filler:
                text_part = capitalize_first_alpha(text_part)

            # Reassemble: keep tag exactly as it was (everything up to and including the first '>')
            tag = line.split(">", 1)[0]
            line = tag + ">" + text_part

        # else: leave line untouched (timestamps, NOTE CONF, headers, etc.)
        cleaned_lines.append(line)

    # Fix conjunctions AFTER cleaning (needs line context)
    cleaned_lines = fix_conjunction_across_lines(cleaned_lines)

    with open(output_path, "w", encoding="utf-8") as f:
        f.writelines(cleaned_lines)

    print(f"\n✔ Cleaning complete.\nSaved → {output_path}\n")

