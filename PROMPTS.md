# PROMPTS.md: Nykaa Agent Gatekeeper (PGD202564619)

## Main instructions I gave the coding agent (Antigravity, Claude Sonnet 4.6)

### 14 Nov 2026: Decision logic
Prompt: "<PASTE YOUR EXACT ORIGINAL PROMPT HERE>"
Result: The agent created gatekeeper.py and test_gatekeeper.py (14 test cases).
Problem found later: the code did not match RULES.md (see below).

### 19 Nov 2026: Review and fix (Claude chat, not Antigravity)
Prompt: "review and let me know the next steps. help me complete my assignment."
Then: "yes" (to the offer to fix decide(), the tests, PROMPTS.md and .gitignore).
Result: Claude reviewed all files, ran the tests and found the mismatch, then
produced corrected gatekeeper.py, test_gatekeeper.py, PROMPTS.md and .gitignore.

## Things I checked or changed myself

- 14 Nov 2026: I tried `python gatekeeper.py enrolled place_order 4500` and
  noted ALLOW under Rule 7. **This note was wrong.** The command was invalid
  (the CLI needs `decide <customer> <agent> <action> [amount]`), and the
  original code used a Rs 2,000 limit, so it would not have allowed 4,500.
- 19 Nov 2026: I ran test_gatekeeper.py against the original code. 10 of 14
  tests failed because gatekeeper.py did not follow RULES.md:
  - LIMIT was Rs 2,000 instead of Rs 5,000.
  - Rule numbers were different (unregistered was 1, revoked was 7,
    view_order was 2, and so on).
  - Refunds were always ASK CUSTOMER, even up to Rs 5,000.
- 19 Nov 2026: Fix: rewrote decide() to follow RULES.md top to bottom,
  set LIMIT = 5_000, and updated the comments. I also added 4 edge-case tests
  (18 in total). All 18 pass.
- 19 Nov 2026: Re-ran the correct command:
  `python gatekeeper.py register cust_01 agent_A`, then
  `python gatekeeper.py decide cust_01 agent_A place_order 4500`.
  Result: ALLOW under Rule 7, because 4,500 is within the Rs 5,000 limit.
  A 7,000 order gave ASK CUSTOMER (Rule 6). A revoked agent was BLOCKED
  under Rule 3. Full output is in demo_output.txt.
