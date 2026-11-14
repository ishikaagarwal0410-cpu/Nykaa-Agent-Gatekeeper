# PROMPTS.md: Nykaa Agent Gatekeeper (PGD202564619)

## Main instructions I gave the coding agent (Antigravity, Claude Sonnet 4.6)

### 14 Nov 2026: Decision logic
Prompt: "<your pasted prompt stays here>"
Result: The agent created gatekeeper.py and test_gatekeeper.py (10 test cases).

## Things I checked or changed myself

- 14 Nov 2026: I ran `python gatekeeper.py enrolled place_order 4500`. The result was
  ALLOW under Rule 7, because 4,500 is under the Rs 5,000 limit.
