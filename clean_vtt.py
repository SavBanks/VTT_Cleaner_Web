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

MEDICAL_TERMS = [
    "USP", "FDA", "DEA", "CDC", "NIH", "HIPAA",
    "NDC", "CMS", "CLIA", "EMR", "EHR", "HCP", "MSL",
    "RA", "PK", "PD", "IRB", "PI", "API",
    "MEDICARE", "MEDICAID", "VA", "DOD",
    "HEOR", "ICER", "QALY", "MTM",
    "ONCOLOGY", "CARDIOLOGY", "NEUROLOGY", "PHARMACOLOGY"
]

# compile medical set for fast checks
_MEDICAL_SET = set(MEDICAL_TERMS)

FILLER_PATTERNS = [
    r"\bum\b", r"\buh\b", r"\ber\b", r"\bumm+\b", r"\buhh+\b",
    r"\byou know\b", r"\bi mean\b", r"\bkind of\b", r"\bsort of\b",
    r"\bso\b", r"\bokay\b", r"\bbasically\b", r"\bactually\b", r"\bliterally\b"
]

# combined regex to detect leading filler quickly (used to check original start)
_LEADING_FILLER_RE = re.compile(r'^\s*(?:' + '|'.join(p.strip(r'\b') for p in FILLER_PATTERNS) + r')', flags=re.IGNORECASE)

NUM_WORDS = {
    "1": "one", "2": "two", "3": "three", "4": "four",
    "5": "five", "6": "six", "7": "seven", "8": "eight", "9": "nine"
}

TIMESTAMP_PATTERN = re.compile(r"\d{1,2}:\d{2}")

# ==========================
#   HELPERS
# ==========================

def remove_filler_words(text):
    for pat in FILLER_PATTERNS:
        text = re.sub(rf"(^|\s){pat}([, ]+|$)", " ", text, flags=re.IGNORECASE)
    # collapse extra spaces
    text = re.sub(r"\s{2,}", " ", text)
    return text.strip()

def remove_unwanted_repeated_I(text):
    # Replace "I, I" (case-insensitive) with a single capital I
    return re.sub(r'\b[Ii]\s*,\s*[Ii]\b', 'I', text)

def convert_single_digits(text):
    # preserve timestamps like 8:30 by skipping patterns with colon
    parts = re.split(r'(\d+:\d+)', text)  # will keep timestamps in the list
    out = []
    for p in parts:
        if TIMESTAMP_PATTERN.fullmatch(p):
            out.append(p)
        else:
            out.append(re.sub(r"\b([1-9])\b", lambda m: NUM_WORDS[m.group(1)], p))
    return "".join(out)

def lowercase_common_words(text):
    def fix(m):
        w = m.group(0)
        if w.lower() in COMMON_LOWER_WORDS:
            return w.lower()
        return w
    return re.sub(r"\b[A-Z][a-z]+\b", fix, text)

def restore_medical_terms(text):
    # restore medical acronyms/titles only when they appear as whole words
    for term in _MEDICAL_SET:
        text = re.sub(rf"\b{re.escape(term)}\b", term, text, flags=re.IGNORECASE)
    return text

def capitalize_first_word_only(text):
    """
    Capitalize only the first word of the line.
    We lowercase the rest of that first word (so it becomes Title-case for the first word).
    """
    if not text:
        return text
    # preserve leading whitespace
    leading_ws = re.match(r'^\s*', text).group(0)
    stripped = text[len(leading_ws):]
    if not stripped:
        return text
    parts = stripped.split(' ', 1)
    first = parts[0]
    rest = parts[1] if len(parts) > 1 else ''
    # capitalize first letter, lowercase the rest of the first word
    if first and first[0].isalpha():
        first = first[0].upper() + first[1:].lower()
    rebuilt = first + ((' ' + rest) if rest else '')
    return leading_ws + rebuilt

def force_lowercase_first_word_if_needed(text):
    """
    When we should NOT capitalize the line start, ensure the first word is not capitalized,
    except when it's a protected item (I pronoun or a medical acronym).
    """
    if not text:
        return text
    leading_ws = re.match(r'^\s*', text).group(0)
    stripped = text[len(leading_ws):]
    if not stripped:
        return text
    parts = stripped.split(' ', 1)
    first = parts[0]
    rest = parts[1] if len(parts) > 1 else ''
    # Check protections
    if first == 'I':
        return text  # keep capital I
    if first.upper() in _MEDICAL_SET:
        # restore exact medical casing (from MEDICAL_TERMS list)
        correct = next((t for t in MEDICAL_TERMS if t.upper() == first.upper()), first)
        return leading_ws + correct + ((' ' + rest) if rest else '')
    # Otherwise lowercase first character (but keep the rest of the word as-is)
    if first and first[0].isalpha():
        first = first[0].lower() + first[1:]
    rebuilt = first + ((' ' + rest) if rest else '')
    return leading_ws + rebuilt

def original_starts_with_filler(orig_text):
    return bool(_LEADING_FILLER_RE.search(orig_text.strip()))

def find_previous_speaker_text(cleaned_lines):
    """
    Scan cleaned_lines backwards and return the first speaker-text portion (without tag).
    Returns None if none found.
    """
    for prev in reversed(cleaned_lines):
        if "<v" in prev and ">" in prev:
            return prev.split(">", 1)[1].strip()
    return None

def fix_conjunction_across_lines(lines):
    new = []
    for i, line in enumerate(lines):
        if i > 0:
            prev = new[-1].rstrip()
            # get first word of current line (after any tag)
            candidate = line.strip()
            # if line is speaker line, skip tag to get first word
            if "<v" in line and ">" in line:
                candidate = line.split(">",1)[1].strip()
            first_word = candidate.split(" ")[0].lower() if candidate else ""
            if first_word in CONJUNCTIONS:
                if prev and prev[-1] not in ".?!,":
                    new[-1] = prev + ","
                # remove stray comma after conjunction
                line = re.sub(rf"^({first_word}),\s*", rf"\1 ", line, flags=re.IGNORECASE)
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

        # Preserve untouched lines exactly (timestamps, NOTE blocks, headers, blank lines)
        if (stripped == "" or
            stripped.startswith("WEBVTT") or
            "-->" in line or
            stripped.startswith("NOTE") or
            stripped.startswith("{") or
            stripped.startswith("}")):
            cleaned.append(line)
            continue

        # Process only speaker lines with a tag <v ...>
        if "<v" in line and ">" in line:
            tag, after = line.split(">", 1)
            orig_after = after.rstrip("\n")  # original spoken text (keep for filler detection)

            # Determine previous speaker line's final punctuation status
            prev_speaker_text = find_previous_speaker_text(cleaned)
            prev_ends_sentence = False
            if prev_speaker_text:
                prev_ends_sentence = prev_speaker_text.endswith(('.', '?', '!'))

            # Determine whether original started with a filler (Um, etc.)
            started_with_filler = original_starts_with_filler(orig_after)

            # Cleaning pipeline (do not finalize capitalization yet)
            text = orig_after

            text = remove_filler_words(text)
            text = remove_unwanted_repeated_I(text)
            text = convert_single_digits(text)
            text = lowercase_common_words(text)
            text = restore_medical_terms(text)

            # Now apply capitalization rule:
            if prev_ends_sentence or started_with_filler:
                # Capitalize the first word (safe)
                text = capitalize_first_word_only(text)
            else:
                # Do NOT capitalize the first word — force lowercase if not protected
                text = force_lowercase_first_word_if_needed(text)

            # Reassemble, preserving the same tag and newline behavior
            # Keep trailing newline if original had it
            newline = "\n" if line.endswith("\n") else ""
            cleaned.append(tag + ">" + text + newline)
            continue

        # All other lines — keep exactly as-is
        cleaned.append(line)

    # Fix conjunctions (needs context across lines)
    cleaned = fix_conjunction_across_lines(cleaned)

    # Write back preserving exact spacing and line count
    with open(output_path, "w", encoding="utf-8") as f:
        f.writelines(cleaned)

    print(f"\n✔ Cleaning complete.\nSaved → {output_path}\n")
