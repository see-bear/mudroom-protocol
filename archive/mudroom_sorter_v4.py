import os
from datetime import datetime

def load_keywords(path):
    with open(path, 'r', encoding='utf-8') as f:
        return [line.strip().lower() for line in f if line.strip()]

emoji_keywords = {
    "✅": "L2",
    "💡": "L3",
    "🎯": "L3",
    "🐛": "L1",
    "❓": "L1",
    "📌": "L2"
}

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

    # Use file's last modified date for tag
    file_date = datetime.fromtimestamp(os.path.getmtime(input_path)).strftime("%Y-%m-%d")
    output_folder = os.path.join(output_dir, file_date)
    os.makedirs(output_folder, exist_ok=True)

    outputs = {"L1": [], "L2": [], "L3": []}

    with open(input_path, "r", encoding="utf-8") as f:
        lines = f.readlines()

    for i, line in enumerate(lines, start=1):
        score, label = score_line(line, level_keywords, use_emoji)
        if score > 0 and label in outputs:
            outputs[label].append(f"[{label}] ({score}) Line {i}: {line.strip()}\n")

    for level, content in outputs.items():
        if content:
            file_root = os.path.splitext(os.path.basename(input_path))[0]
            out_path = os.path.join(output_folder, f"{file_date}-{file_root}-{level}.md")
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
