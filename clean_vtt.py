import re

# ==========================
#  CONFIGURATION LISTS
# ==========================

CONJUNCTIONS = ["and", "but", "or", "nor", "yet", "so"]

COMMON_LOWER_WORDS = set([
    "the","and","but","or","nor","for","yet","so","a","an","to","in","on","at","by",
    "from","with","of","as","that","this","these","those","is","are","was","were",
    "be","been","being","it","its","if","then","else","also","not","very","just",
    "such","than","because","when","where","while","however","therefore","thus",
    "although","though","unless","until","whether","like","unlike","about","above",
    "below","under","over","again","already","still","even","too","very","maybe",
    "perhaps","almost","nearly","basically","actually","literally","really",
    "kind","sort","part","might","should","could","would","will","can","may",
    "shall","up","down","out","into","through","across","between","among",
])

# Medical terms / acronyms that stay exactly as typed (case-insensitive matching)
MEDICAL_TERMS = [
    "USP", "FDA", "DEA", "CDC", "NIH", "HIPAA",
    "NDC", "CMS", "CLIA", "EMR", "EHR", "HCP", "MSL",
    "RA", "PK", "PD", "IRB", "PI", "API",
    "Medicare", "Medicaid", "VA", "DoD",
    "HEOR", "ICER", "QALY", "MTM"
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
#   CLEANING HELPERS
# ==========================

def remove_filler_words(text: str) -> str:
    for pat in FILLER_PATTERNS:
        # remove filler word with optional commas/spaces around it
        text = re.sub(rf"[, ]*\b{pat}\b[, ]*", " ", text, flags=re.IGNORECASE)
    return text

def collapse_repeated_words_within(text: str) -> str:
    # remove simple repeated tokens within a line (e.g., "that that" -> "that")
    while True:
        new = re.sub(r"\b(\w+)(?:[\s,;:-]+)\1\b", r"\1", text, flags=re.IGNORECASE)
        if new == text:
            break
        text = new
    return text

def convert_single_digits(text: str) -> str:
    return re.sub(r"\b([1-9])\b",
                  lambda m: NUM_WORDS[m.group(1)], text)

def lowercase_common_midsentence(text: str, protect_first_word: bool=False) -> str:
    """
    Lowercase common words that are capitalized mid-sentence.
    If protect_first_word is True, the first alpha token of the line is NOT lowercased
    (useful when capitalization will be applied later).
    """
    # split into tokens while preserving whitespace
    tokens = re.split(r'(\s+)', text)
    result = []
    first_alpha_seen = False

    for t in tokens:
        if t.isspace() or t == "":
            result.append(t)
            continue

        # alpha token?
        m = re.match(r"^([A-Za-z]+)(.*)$", t)
        if not m:
            # punctuation or mixed token: keep as is
            result.append(t)
            # if it contains sentence-ending punctuation, reset first_alpha_seen
            if any(ch in ".!?" for ch in t):
                first_alpha_seen = False
            continue

        word, tail = m.group(1), m.group(2)

        if not first_alpha_seen:
            # first alpha word in this line
            if protect_first_word:
                # keep as-is to allow later capitalization
                result.append(word + tail)
            else:
                # apply normal lowercasing rules (but don't touch protected medical terms)
                if word.lower() in COMMON_LOWER_WORDS and word.lower() not in [p.lower() for p in MEDICAL_TERMS]:
                    result.append(word.lower() + tail)
                else:
                    result.append(word + tail)
            first_alpha_seen = True
        else:
            # subsequent alpha words in line
            if word.isupper():
                # probably acronym — keep
                result.append(word + tail)
            elif word.lower() in COMMON_LOWER_WORDS and word.lower() not in [p.lower() for p in MEDICAL_TERMS]:
                result.append(word.lower() + tail)
            else:
                result.append(word + tail)

        # sentence end check in tail
        if any(ch in ".!?" for ch in tail):
            first_alpha_seen = False

    return "".join(result)

def restore_medical_terms(text: str) -> str:
    # attempt to restore casing for known medical terms (case-insensitive match)
    for term in MEDICAL_TERMS:
        # replace case-insensitive occurrences with the canonical casing
        text = re.sub(r'\b' + re.escape(term) + r'\b', term, text, flags=re.IGNORECASE)
    return text

# -----------------------------------------
# Conjunction fixes across lines (may append comma to previous line)
# -----------------------------------------
def fix_conjunction_across_lines(lines):
    new_lines = []
    for i, line in enumerate(lines):
        if i > 0:
            prev = new_lines[-1].rstrip()
            # find first word of current line (skip leading speaker tag if present)
            stripped = line.strip()
            first_word = ""
            # get first word token (letters) if exists
            m = re.match(r"^(?:<v[^>]*>)?\s*([A-Za-z]+)", stripped)
            if m:
                first_word = m.group(1).lower()
            if first_word in CONJUNCTIONS:
                # add comma to previous line if it doesn't end with punctuation or comma
                if prev and prev[-1] not in ".?!,":
                    new_lines[-1] = prev + ","
                # remove stray comma after conjunction at start of this line (i.e., "and, again" should remain if intentional)
                # only remove if it is immediately "and," followed by space and a lowercase word — conservative
                pattern = rf"^(<v[^>]*>)?\s*({re.escape(first_word)}),\s+"
                line = re.sub(pattern, lambda m: (m.group(1) or "") + m.group(2) + " ", line, flags=re.IGNORECASE)

        new_lines.append(line)
    return new_lines

# -----------------------------------------
# Capitalize start of lines if previous line ended in sentence punctuation
# -----------------------------------------
def capitalize_after_punctuation(lines):
    new_lines = []
    for i, line in enumerate(lines):
        if i == 0:
            new_lines.append(line)
            continue

        prev = new_lines[-1].rstrip()
        cur = line

        if prev.endswith((".", "?", "!")):
            # Only act on speaker text lines (those that contain <v ...)
            if "<v" in cur:
                parts = cur.split(">", 1)
                if len(parts) == 2:
                    tag, text = parts
                    # find first alphabetical char and uppercase it
                    # preserve any leading spaces
                    leading_ws = re.match(r"^(\s*)", text).group(1)
                    core = text[len(leading_ws):]
                    if core:
                        # uppercase first alpha char in core
                        m = re.search(r"[A-Za-z]", core)
                        if m:
                            idx = m.start()
                            core = core[:idx] + core[idx].upper() + core[idx+1:]
                        new_text = leading_ws + core
                        cur = tag + ">" + new_text
        new_lines.append(cur)
    return new_lines

# ==========================
#  MAIN CLEANING FUNCTION
# ==========================
def clean_vtt_file(input_path, output_path):
    with open(input_path, "r", encoding="utf-8") as f:
        lines = f.readlines()

    # 1) Per-line core cleaning (keep tag + text)
    cleaned_lines = []
    for line in lines:
        if "<v" in line:
            # split tag from text, keep tag exactly as-is
            parts = line.split(">", 1)
            if len(parts) == 2:
                tag, text = parts
                # core per-line cleaning
                text = remove_filler_words(text)
                text = collapse_repeated_words_within(text)
                text = convert_single_digits(text)
                # Protect first word from lowercasing for now (we'll handle capitalization after line-level fixes)
                text = lowercase_common_midsentence(text, protect_first_word=True)
                text = restore_medical_terms(text)
                new_line = tag + ">" + text
            else:
                new_line = line
        else:
            new_line = line
        cleaned_lines.append(new_line)

    # 2) Fix conjunctions across lines (this may add commas to previous lines)
    cleaned_lines = fix_conjunction_across_lines(cleaned_lines)

    # 3) Capitalize after punctuation now that conjunction changes are final
    cleaned_lines = capitalize_after_punctuation(cleaned_lines)

    # 4) After capitalization, we can do a final pass to lowercase mid-sentence words
    #    while NOT lowercasing first alphabetical token if it was capitalized by step 3.
    final_lines = []
    for i, line in enumerate(cleaned_lines):
        if "<v" in line:
            parts = line.split(">", 1)
            tag, text = parts
            # If previous line ended with punctuation, we should protect first word from lowercasing.
            prev_ends_sentence = False
            if i > 0:
                prev_ends_sentence = cleaned_lines[i-1].rstrip().endswith((".", "?", "!"))
            text = lowercase_common_midsentence(text, protect_first_word=prev_ends_sentence)
            text = restore_medical_terms(text)
            final_lines.append(tag + ">" + text)
        else:
            final_lines.append(line)

    # 5) Write out
    with open(output_path, "w", encoding="utf-8") as f:
        f.writelines(final_lines)

    print(f"\n✔ Cleaning complete.\nSaved → {output_path}\n")
