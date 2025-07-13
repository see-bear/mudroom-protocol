import os
import re
from datetime import datetime
from dateutil.parser import parse as date_parse

# Settings
SOURCE_DIR = "batch_txts"
OUTPUT_DIR = "mudroom_logs"

# Heuristic keyword categories
L1_KEYWORDS = ["debug", "error", "fix", "workflow", "React", "server", "endpoint", "schema"]
L2_KEYWORDS = ["done", "confirmed", "verified", "complete", "working", "finished"]
L3_KEYWORDS = ["decision", "we will", "we've agreed", "going forward", "strategically", "goal", "direction", "plan", "final choice"]
TODO_KEYWORDS = ["todo", "to-do", "follow up", "next step", "unfinished"]

def extract_date(text):
    patterns = [r'\b\d{4}-\d{2}-\d{2}\b', r'\b\d{4}/\d{2}/\d{2}\b']
    for p in patterns:
        match = re.search(p, text)
        if match:
            try:
                return date_parse(match.group()).strftime("%Y-%m-%d")
            except:
                continue
    return datetime.now().strftime("%Y-%m-%d")

def classify_block(text):
    ltext = text.lower()
    scores = {"L1": 0, "L2": 0, "L3": 0}
    for w in L1_KEYWORDS:
        if w in ltext:
            scores["L1"] += 1
    for w in L2_KEYWORDS:
        if w in ltext:
            scores["L2"] += 1
    for w in L3_KEYWORDS:
        if w in ltext:
            scores["L3"] += 1
    best = max(scores, key=scores.get)
    return best if scores[best] > 0 else None

def extract_todos(lines):
    return [line.strip() for line in lines if any(k in line.lower() for k in TODO_KEYWORDS)]

def classify_transcript(path):
    with open(path, "r", encoding="utf-8") as f:
        lines = f.readlines()

    blocks, current = [], []
    for line in lines:
        if line.strip() == "":
            if current:
                blocks.append(" ".join(current).strip())
                current = []
        else:
            current.append(line.strip())
    if current:
        blocks.append(" ".join(current).strip())

    out = {"L1": [], "L2": [], "L3": []}
    todos = extract_todos(lines)
    for blk in blocks:
        label = classify_block(blk)
        if label:
            out[label].append(blk + "\n")

    date = extract_date("\n".join(lines))
    out_dir = os.path.join(OUTPUT_DIR, date)
    os.makedirs(out_dir, exist_ok=True)
    basename = os.path.splitext(os.path.basename(path))[0]

    for level in ["L1", "L2", "L3"]:
        with open(os.path.join(out_dir, f"{basename}-{level}.md"), "w", encoding="utf-8") as f:
            f.writelines(out[level])

    with open(os.path.join(out_dir, f"{basename}-todos.yaml"), "w", encoding="utf-8") as f:
        for t in todos:
            f.write(f"- {t}\n")

    with open(os.path.join(out_dir, f"{basename}-session-load.txt"), "w", encoding="utf-8") as f:
        f.write("## Vision (L3)\n\n")
        f.writelines(out["L3"])
        f.write("\n\n## Open Tasks\n\n")
        f.writelines(f"- {t}\n" for t in todos)

    print(f"✅ Processed: {os.path.basename(path)} → {out_dir}")

if __name__ == "__main__":
    for fname in os.listdir(SOURCE_DIR):
        if fname.endswith(".txt"):
            classify_transcript(os.path.join(SOURCE_DIR, fname))