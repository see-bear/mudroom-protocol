import os
import re
from datetime import datetime
from dateutil.parser import parse as date_parse

# Heuristic keyword categories
L1_KEYWORDS = ["debug", "error", "fix", "workflow", "React", "server", "endpoint", "schema"]
L2_KEYWORDS = ["done", "confirmed", "verified", "complete", "working", "finished"]
L3_KEYWORDS = ["decision", "we will", "we've agreed", "going forward", "strategically", "goal", "direction", "plan", "final choice"]
TODO_KEYWORDS = ["todo", "to-do", "follow up", "next step", "unfinished"]

# Determine date
def extract_date(text):
    patterns = [r'\b\d{4}-\d{2}-\d{2}\b', r'\b\d{4}/\d{2}/\d{2}\b']
    dates = []
    for p in patterns:
        dates += re.findall(p, text)
    if dates:
        try:
            return date_parse(dates[-1]).strftime("%Y-%m-%d")
        except:
            pass
    return datetime.now().strftime("%Y-%m-%d")

# Classify block
def classify_block(text):
    ltext = text.lower()
    scores = {"L1": 0, "L2": 0, "L3": 0}
    for word in L1_KEYWORDS:
        if word in ltext:
            scores["L1"] += 1
    for word in L2_KEYWORDS:
        if word in ltext:
            scores["L2"] += 1
    for word in L3_KEYWORDS:
        if word in ltext:
            scores["L3"] += 1
    best = max(scores, key=scores.get)
    return best if scores[best] > 0 else None

def extract_todos(lines):
    return [line for line in lines if any(k in line.lower() for k in TODO_KEYWORDS)]

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
    out_dir = os.path.join("gpt_classified", date)
    os.makedirs(out_dir, exist_ok=True)

    for level in ["L1", "L2", "L3"]:
        with open(os.path.join(out_dir, f"{level}.md"), "w", encoding="utf-8") as f:
            f.writelines(out[level])

    with open(os.path.join(out_dir, "todos.yaml"), "w", encoding="utf-8") as f:
        for t in todos:
            f.write(f"- {t.strip()}\n")

    with open(os.path.join(out_dir, "session-load.txt"), "w", encoding="utf-8") as f:
        f.write("## Vision (L3)\n\n")
        f.writelines(out["L3"])
        f.write("\n\n## Open Tasks\n\n")
        f.writelines(f"- {t.strip()}\n" for t in todos)

    print(f"✅ Done. Output in: {out_dir}")

if __name__ == "__main__":
    import sys
    if len(sys.argv) != 2:
        print("Usage: python gpt_classifier_enhanced.py transcript.txt")
    else:
        classify_transcript(sys.argv[1])