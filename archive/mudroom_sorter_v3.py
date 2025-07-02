import os
from datetime import datetime

def load_keywords(path):
    with open(path, 'r', encoding='utf-8') as f:
        return [line.strip().lower() for line in f if line.strip()]

# Optional emoji-to-level mapping
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

    # Emoji parsing
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

    date_tag = datetime.now().strftime("%Y-%m-%d")
    output_folder = os.path.join(output_dir, date_tag)
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
            out_path = os.path.join(output_folder, f"{date_tag}-{level}.md")
            with open(out_path, "w", encoding="utf-8") as f:
                f.writelines(content)

    print(f"Sorting complete. Output saved to: {output_folder}")

if __name__ == "__main__":
    classify_file(
        input_path="sample_chat.txt",
        keywords_dir="keywords",
        output_dir="mudroom_logs",
        use_emoji=True  # Toggle this to False to disable emoji parsing
    )
