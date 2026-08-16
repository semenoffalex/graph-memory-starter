"""UserPromptSubmit hook. additionalContext is the injection."""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from recall import recall

prompt = json.load(sys.stdin).get("prompt", "")
facts = recall(prompt, hops=3, top_k=8)
text = facts.as_text()

print(json.dumps({
    "systemMessage": text.split("\n")[0],  # shown to the user at submit
    "hookSpecificOutput": {
        "hookEventName": "UserPromptSubmit",
        "additionalContext": text,
    }
}))
