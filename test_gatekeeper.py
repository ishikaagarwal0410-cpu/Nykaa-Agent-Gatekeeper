"""
Quick regression test for all 7 rules.
Run with: python test_gatekeeper.py
"""
import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from gatekeeper import decide, LIMIT

PASS = "\033[32mPASS\033[0m"
FAIL = "\033[31mFAIL\033[0m"

cases = [
    # (description,           agent_status, action,        amount, expected_decision, expected_rule)
    ("Rule 1 – bad action",   "enrolled",  "buy_now",      0,      "BLOCK",          1),
    ("Rule 1 – missing amt",  "enrolled",  "place_order",  0,      "BLOCK",          1),
    ("Rule 2 – unregistered", "unknown",   "view_order",   0,      "BLOCK",          2),
    ("Rule 3 – revoked",      "revoked",   "view_order",   0,      "BLOCK",          3),
    ("Rule 4 – view_order",   "enrolled",  "view_order",   0,      "ALLOW",          4),
    ("Rule 5 – return",       "enrolled",  "return",       0,      "ASK CUSTOMER",   5),
    ("Rule 6 – order >limit", "enrolled",  "place_order",  7000,   "ASK CUSTOMER",   6),
    ("Rule 6 – refund >limit","enrolled",  "refund",       5001,   "ASK CUSTOMER",   6),
    ("Rule 7 – order <=limit","enrolled",  "place_order",  5000,   "ALLOW",          7),
    ("Rule 7 – refund <=limit","enrolled", "refund",       4999,   "ALLOW",          7),
]

all_passed = True
print(f"\n{'Case':<30} {'Got':<14} {'Rule':>4}  {'Status'}")
print("-" * 65)
for desc, status, action, amount, exp_dec, exp_rule in cases:
    r = decide(status, action, amount)
    ok = r["decision"] == exp_dec and r["rule"] == exp_rule
    all_passed = all_passed and ok
    tag = PASS if ok else FAIL
    print(f"{desc:<30} {r['decision']:<14} #{r['rule']:>1}      {tag}")

print()
if all_passed:
    print("All tests passed ✓")
else:
    print("Some tests FAILED ✗")
    sys.exit(1)
