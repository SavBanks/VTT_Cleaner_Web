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
    "USP", "FDA", "DEA", "CDC", "NIH", "HIPAA",
    "NDC", "CMS", "CLIA", "EMR", "EHR", "HCP", "MSL",
    "RA", "PK", "PD", "IRB", "PI", "API",
    "Medicare", "Medicaid", "VA", "DoD",
    "HEOR", "ICER", "QALY", "MTM",
    "Oncology", "Cardiology", "Neurology", "Pharmacology",
]

FILLER_PATTERNS = [
    r"\bum\b", r"\buh\b", r"\ber\b",
    r"\bumm+\b", r"\buhh+\b",
    r"\byou know\b",
    r"\bi mean\b",
    r"\bkind of\b",
    r"\bsort of\b",
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
# HELPER DETECTORS
# ==========================

def is_timestamp(line):
    return bool(re.match(r"^\d{2}:\d{2}:\d{2}\.\d{3} --> \d{2}:\d{2}:\d{2}\.\d{3}$", line.strip()))

def is_note_line(line):
    return line.strip().startswith("NOTE")

def starts_with_speaker(line):
    return "<v" in line

# ==========================
#  CLEANING FUNCTIONS
# ==========================

def remove_filler_words(text):
    for pat in FILLER_PATTERNS:
        text = re.sub(rf"[, ]*\b{pat}\b[, ]*", " ", text, flags=re.IGNORECASE)
    return text

def collapse_repeated_words(text):
    # ONLY collapse things like "I, I" or "word, word"
    return re.sub(r"\b(\w+),\s+\1\b", r"\1", text, flags=re.IGNORECASE)

def convert_single_digits(text):
    # Skip times like "8:30"
    return re.sub(
        r"\b([1-9])\b(?!:)", 
        lambda m: NUM_WORDS[m.group(1)],
        text
    )

def lowercase_common_words(text):
    def fix(match):
        word = match.group(0)
        lw = word.lower()
        return lw if lw in COMMON_LOWER_WORDS else word
    return re.sub(r"\b[A-Z][a-z]+\b", fix, text)

def restore_medical_terms(text):
    for term in MEDICAL_TERMS:
        text = re.sub(rf"\b{term}\b", term, text, flags=re.IGNORECASE)
    return text

def smart_capitalize(text):
    if not text:
        return text
    return text[0].upper() + text[1:]

def fix_conjunction_across_lines(lines):
    new_lines = []
    for i, line in enumerate(lines):
        if i > 0:
            prev = new_lines[-1].rstrip()
            first_word = line.strip().split(" ")[0].lower()

            if first_word in CONJUNCTIONS:
                if prev and prev[-1] not in ".?!,":
                    new_lines[-1] = prev + ","
                line = re.sub(rf"^({first_word}),\s*", rf"\1 ", line, flags=re.IGNORECASE)

        new_lines.append(line)
    return new_lines

# ==========================
#  MAIN PROCESSOR
# ==========================

def clean_vtt_text(input_path, output_path):

    with open(input_path, "r", encoding="utf-8") as f:
        lines = f.readlines()

    cleaned_lines = []
    prev_was_sentence_end = True  # Allows capitalization on very first line of text

    for line in lines:
        original_line = line

        # Preserve spacing exactly
        if original_line.strip() == "":
            cleaned_lines.append(original_line)
            continue

        # Preserve timestamps 100% untouched
        if is_timestamp(original_line):
            cleaned_lines.append(original_line)
            continue

        # Preserve NOTE blocks 100% untouched
        if is_note_line(original_line):
            cleaned_lines.append(original_line)
            continue

        # Speaker lines get cleaned only AFTER the ">"
        if starts_with_speaker(original_line):

            speaker_tag, text = original_line.split(">", 1)
            speaker_tag += ">"

            # CLEAN ONLY the text part
            cleaned = text

            before = cleaned
            cleaned = remove_filler_words(cleaned)
            filler_was_removed = (cleaned != before)

            cleaned = collapse_repeated_words(cleaned)
            cleaned = convert_single_digits(cleaned)
            cleaned = lowercase_common_words(cleaned)
            cleaned = restore_medical_terms(cleaned)

            # Smart capitalization:
            if filler_was_removed:
                cleaned = smart_capitalize(cleaned)
            else:
                if prev_was_sentence_end:
                    cleaned = smart_capitalize(cleaned)

            prev_was_sentence_end = cleaned.rstrip().endswith((".", "?", "!"))

            cleaned_lines.append(speaker_tag + cleaned)
            continue

        # Any other lines: keep unchanged
        cleaned_lines.append(original_line)

    cleaned_lines = fix_conjunction_across_lines(cleaned_lines)

    with open(output_path, "w", encoding="utf-8") as f:
        f.writelines(cleaned_lines)

    print(f"\n✔ Cleaning complete. Saved → {output_path}\n")
