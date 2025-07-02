import os
import re
from datetime import datetime
from dateutil.parser import parse as date_parse

def load_keywords(path):
    with open(path, 'r', encoding='utf-8') as f:
        return [line.strip().lower() for line in f if line.strip()]

emoji_keywords = {
    "✅": "L2",
    "💡": "L3",
    "🎯": "L3",
    "🐛": "L1",
    "❓": "L1",
    "📌": "L2",
    "🧠": "L3"
}

# Regex patterns for various date formats
date_patterns = [
    r'\b\d{4}-\d{2}-\d{2}\b',       # YYYY-MM-DD
    r'\b\d{4}/\d{2}/\d{2}\b',       # YYYY/MM/DD
    r'\b(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*[\s]+\d{1,2},[\s]+\d{4}\b'  # Month D, YYYY
]

def extract_latest_date(text):
    found_dates = []
    for pattern in date_patterns:
        matches = re.findall(pattern, text, flags=re.IGNORECASE)
        for m in matches:
            try:
                parsed = date_parse(m, fuzzy=True)
                found_dates.append(parsed)
            except Exception:
                continue
    if found_dates:
        return max(found_dates).strftime('%Y-%m-%d')
    return datetime.now().strftime('%Y-%m-%d')

def score_line(line, level_keywords, use_emoji=True):
    line_l = line.lower()
    if line_l.startswith(('strategy:', 'work:', 'churn:')):
        return 100, line_l.split(':', 1)[0].upper()

    scores = {level: sum(kw in line_l for kw in kws) for level, kws in level_keywords.items()}

    if use_emoji:
        for emoji, level in emoji_keywords.items():
            if emoji in line:
                scores[level] += 1

    best_level = max(scores, key=scores.get)
    match_count = scores[best_level]

    if match_count >= 2:
        return 75, best_level
    elif match_count == 1:
        return 60, best_level
    return 0, "UNCLASSIFIED"

def classify_file(input_path, keywords_dir, output_dir, use_emoji=True):
    level_keywords = {
        "L1": load_keywords(os.path.join(keywords_dir, "level1.txt")),
        "L2": load_keywords(os.path.join(keywords_dir, "level2.txt")),
        "L3": load_keywords(os.path.join(keywords_dir, "level3.txt"))
    }

    with open(input_path, "r", encoding="utf-8") as f:
        text = f.read()
        lines = text.splitlines()

    date_tag = extract_latest_date(text)
    output_folder = os.path.join(output_dir, date_tag)
    os.makedirs(output_folder, exist_ok=True)

    outputs = {"L1": [], "L2": [], "L3": []}

    for i, line in enumerate(lines, start=1):
        score, label = score_line(line, level_keywords, use_emoji)
        if score > 0 and label in outputs:
            outputs[label].append(f"[{label}] ({score}) Line {i}: {line.strip()}\n")

    for level, content in outputs.items():
        if content:
            file_root = os.path.splitext(os.path.basename(input_path))[0]
            out_path = os.path.join(output_folder, f"{date_tag}-{file_root}-{level}.md")
            with open(out_path, "w", encoding="utf-8") as f:
                f.writelines(content)

    print(f"Processed: {os.path.basename(input_path)} → {output_folder}")

def batch_process_folder(source_dir, keywords_dir, output_dir):
    for fname in os.listdir(source_dir):
        if fname.endswith(".txt"):
            classify_file(
                input_path=os.path.join(source_dir, fname),
                keywords_dir=keywords_dir,
                output_dir=output_dir,
                use_emoji=True
            )

if __name__ == "__main__":
    batch_process_folder(
        source_dir="batch_txts",
        keywords_dir="keywords",
        output_dir="mudroom_logs"
    )
