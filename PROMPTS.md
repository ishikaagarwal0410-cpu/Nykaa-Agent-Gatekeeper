# PROMPTS.md: Nykaa Agent Gatekeeper (PGD202564619)

## Main instructions I gave the coding agent (Antigravity, Claude Sonnet 4.6)

### 14 Nov 2026: Decision logic
Prompt: Exact wording not saved. I asked Antigravity to build a Python gatekeeper
for the Nykaa agent based on my RULES.md, with a decision function, CLI commands
and a test file.
Result: The agent created gatekeeper.py and test_gatekeeper.py (14 test cases).
Problem found later: the code did not match RULES.md (see below).

### 19 Nov 2026: Review and repair (Antigravity)
Prompt: Exact wording not saved. I asked Antigravity to review and repair
gatekeeper.py and its tests.
Result: The agent edited gatekeeper.py and test_gatekeeper.py. I then checked
the final files against RULES.md and re-ran the tests myself.

### 19 Nov 2026: Review help (Claude chat)
Prompt: "review and let me know the next steps. help me complete my assignment."
Result: Claude reviewed my files, ran the tests and found that gatekeeper.py
did not follow RULES.md. It produced corrected versions of gatekeeper.py,
test_gatekeeper.py, PROMPTS.md and .gitignore, which I used after checking them.

## Things I checked or changed myself

- 14 Nov 2026: I tried `python gatekeeper.py enrolled place_order 4500` and
  noted ALLOW under Rule 7. This note was wrong. The command was invalid
  (the CLI needs `decide <customer> <agent> <action> [amount]`), and the
  original code used a Rs 2,000 limit, so it would not have allowed 4,500.
- 19 Nov 2026: Claude's review found that 10 of the 14 tests failed against
  the original gatekeeper.py because LIMIT was Rs 2,000 instead of Rs 5,000,
  the rule numbers were different, and refunds were always ASK CUSTOMER.
- 19 Nov 2026: The fix rewrote decide() to follow RULES.md top to bottom,
  set LIMIT = 5_000 and added 4 edge-case tests (18 in total).
- 19 Nov 2026: I ran `python test_gatekeeper.py` on my own computer.
  All 18 tests passed.
- 19 Nov 2026: I ran the demo commands myself: register cust_01 agent_A,
  then decide place_order 4500 gave ALLOW under Rule 7 (within the Rs 5,000
  limit), place_order 7000 gave ASK CUSTOMER (Rule 6), and a revoked agent
  was BLOCKED (Rule 3). Results are saved in audit_log.csv.