# The Mud Room
*A Human-AI Process for Meaningful Forgetting and Intentional Remembering*

...

## 📎 Appendix: Scoring Script Logic (Sketch)
A future CLI script might follow logic like this:

```python
# Pseudocode for Mud Room scoring and tagging

def score_line(line, level_keywords):
    if line.startswith(('strategy:', 'work:', 'churn:')):
        return 100
    match_count = sum(kw in line for kw in level_keywords)
    if match_count >= 2:
        return 75
    if match_count == 1:
        return 60
    return 0
```

This scoring logic could be applied line-by-line or chunk-by-chunk to automatically split session logs into levels. Chunking would be further improved by using the **Conversational Parse Markers** described above.

---