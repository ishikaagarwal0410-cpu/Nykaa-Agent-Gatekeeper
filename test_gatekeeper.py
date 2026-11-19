"""
test_gatekeeper.py – Regression tests for all 7 rules.

Tests decide() directly (pure logic, no file I/O) so they run
without touching agents.json or audit_log.csv.

Run with:  python test_gatekeeper.py
"""
import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from gatekeeper import decide, LIMIT

GREEN = "\033[32m"
RED   = "\033[31m"
RESET = "\033[0m"
PASS  = f"{GREEN}PASS{RESET}"
FAIL  = f"{RED}FAIL{RESET}"

cases = [
    # description                agent_status    action         amount  exp_decision   exp_rule
    ("Rule 1 – bad action",      "enrolled",     "buy_now",     0,      "BLOCK",       1),
    ("Rule 1 – missing amount",  "enrolled",     "place_order", 0,      "BLOCK",       1),
    ("Rule 1 – zero refund",     "enrolled",     "refund",      0,      "BLOCK",       1),
    ("Rule 2 – unregistered",    "unregistered", "view_order",  0,      "BLOCK",       2),
    ("Rule 3 – revoked",         "revoked",      "view_order",  0,      "BLOCK",       3),
    ("Rule 3 – revoked w/amt",   "revoked",      "place_order", 100,    "BLOCK",       3),
    ("Rule 4 – view_order",      "enrolled",     "view_order",  0,      "ALLOW",       4),
    ("Rule 5 – return",          "enrolled",     "return",      0,      "ASK CUSTOMER",5),
    ("Rule 6 – order >limit",    "enrolled",     "place_order", 7000,   "ASK CUSTOMER",6),
    ("Rule 6 – refund >limit",   "enrolled",     "refund",      5001,   "ASK CUSTOMER",6),
    ("Rule 6 – exactly 1 over",  "enrolled",     "place_order", 5001,   "ASK CUSTOMER",6),
    ("Rule 7 – order at limit",  "enrolled",     "place_order", 5000,   "ALLOW",       7),
    ("Rule 7 – refund below",    "enrolled",     "refund",      4999,   "ALLOW",       7),
    ("Rule 7 – small order",     "enrolled",     "place_order", 500,    "ALLOW",       7),
    # edge cases: first matching rule wins
    ("Edge – revoked + bad act", "revoked",      "buy_now",     0,      "BLOCK",       1),
    ("Edge – unreg + bad act",   "unregistered", "buy_now",     0,      "BLOCK",       1),
    ("Edge – negative order",    "enrolled",     "place_order", -50,    "BLOCK",       1),
    ("Edge – revoked return",    "revoked",      "return",      0,      "BLOCK",       3),
]

all_passed = True
print(f"\n{'Case':<32} {'Expected':<14} {'Got':<14} {'Rule':>4}  Status")
print("-" * 75)

for desc, status, action, amount, exp_dec, exp_rule in cases:
    r = decide(status, action, amount)
    ok = r["decision"] == exp_dec and r["rule"] == exp_rule
    all_passed = all_passed and ok
    tag = PASS if ok else FAIL
    print(f"{desc:<32} {exp_dec:<14} {r['decision']:<14} #{r['rule']:>1}      {tag}")

print()
if all_passed:
    print("All tests passed ✓")
else:
    print("Some tests FAILED ✗")
    sys.exit(1)
