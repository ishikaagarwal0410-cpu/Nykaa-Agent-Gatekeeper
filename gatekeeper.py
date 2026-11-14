"""
gatekeeper.py – Nykaa Agent Gatekeeper
Enrolment : PGD202564619

Implements the 7-rule decision engine from RULES.md.
Rules are evaluated strictly top-to-bottom; the first match wins.

Persistent state
----------------
  agents.json    – registry of (customer, agent) pairs with timestamps
  audit_log.csv  – append-only record of every decision made

Sub-commands
------------
  register <customer> <agent>
      Enrol an agent for a customer and save to agents.json.

  revoke <customer> <agent>
      Mark an agent as revoked in agents.json (keeps history).

  decide <customer> <agent> <action> [amount]
      Look up the saved agent status, run the 7 rules, print the
      decision and append a row to audit_log.csv.

  log
      Print the audit log in a readable table.

  agents
      List all entries in agents.json.

Examples
--------
  python gatekeeper.py register cust_01 agent_A
  python gatekeeper.py decide   cust_01 agent_A view_order
  python gatekeeper.py decide   cust_01 agent_A place_order 3000
  python gatekeeper.py decide   cust_01 agent_A place_order 7000
  python gatekeeper.py decide   cust_01 agent_A return
  python gatekeeper.py decide   cust_01 agent_A refund 4999
  python gatekeeper.py revoke   cust_01 agent_A
  python gatekeeper.py decide   cust_01 agent_A view_order
  python gatekeeper.py decide   cust_01 agent_B view_order
  python gatekeeper.py log
  python gatekeeper.py agents
"""

import csv
import json
import os
import sys
from datetime import datetime

# ── Configuration ─────────────────────────────────────────────────────────────

ENROLMENT = "PGD202564619"

# Rule 6 / 7 threshold.
# Nykaa's average order is ~Rs 2,000; Rs 5,000 ≈ 2.5× a normal basket.
# Orders / refunds above this ask the customer; at or below, the agent acts.
LIMIT = 5_000  # Rs

# Valid actions recognised by the gatekeeper
VALID_ACTIONS = {"view_order", "place_order", "return", "refund"}

# Actions that MUST carry a non-zero positive amount
AMOUNT_REQUIRED = {"place_order", "refund"}

# File paths (same directory as this script)
_HERE         = os.path.dirname(os.path.abspath(__file__))
AGENTS_FILE   = os.path.join(_HERE, "agents.json")
AUDIT_FILE    = os.path.join(_HERE, "audit_log.csv")

# CSV column order for the audit log
_AUDIT_COLS = ["timestamp", "customer", "agent", "action",
               "amount", "decision", "rule"]


# ── Agent Registry (agents.json) ──────────────────────────────────────────────

def _load_agents() -> dict:
    """Return the full agents registry dict, or {} if the file doesn't exist."""
    if not os.path.exists(AGENTS_FILE):
        return {}
    with open(AGENTS_FILE, "r", encoding="utf-8") as fh:
        return json.load(fh)


def _save_agents(registry: dict) -> None:
    """Write the registry dict back to agents.json (pretty-printed)."""
    with open(AGENTS_FILE, "w", encoding="utf-8") as fh:
        json.dump(registry, fh, indent=2)


def _agent_key(customer: str, agent: str) -> str:
    """Composite key used inside the registry dict."""
    return f"{customer}::{agent}"


def cmd_register(customer: str, agent: str) -> None:
    """
    Register an agent for a customer.
    Saves status='enrolled' and the current timestamp to agents.json.
    If the pair already exists the status is reset to 'enrolled'
    (useful to re-enrol a previously revoked agent).
    """
    registry = _load_agents()
    key = _agent_key(customer, agent)
    now = _now()

    if key in registry:
        old_status = registry[key]["status"]
        registry[key]["status"]      = "enrolled"
        registry[key]["enrolled_at"] = now
        registry[key].pop("revoked_at", None)   # clear any old revoke stamp
        print(f"  [register] {customer} / {agent}  "
              f"re-enrolled (was: {old_status})  @ {now}")
    else:
        registry[key] = {
            "customer":    customer,
            "agent":       agent,
            "status":      "enrolled",
            "enrolled_at": now,
        }
        print(f"  [register] {customer} / {agent}  enrolled  @ {now}")

    _save_agents(registry)


def cmd_revoke(customer: str, agent: str) -> None:
    """
    Revoke an agent for a customer.
    Sets status='revoked' and stamps revoked_at in agents.json.
    Prints an error if the pair was never registered.
    """
    registry = _load_agents()
    key = _agent_key(customer, agent)

    if key not in registry:
        print(f"  [revoke] ERROR – {customer} / {agent} was never registered.")
        sys.exit(1)

    now = _now()
    registry[key]["status"]     = "revoked"
    registry[key]["revoked_at"] = now
    _save_agents(registry)
    print(f"  [revoke] {customer} / {agent}  revoked  @ {now}")


def _lookup_agent_status(customer: str, agent: str) -> str:
    """
    Return the stored status for (customer, agent):
      'enrolled' | 'revoked' | 'unregistered'
    """
    registry = _load_agents()
    key = _agent_key(customer, agent)
    if key not in registry:
        return "unregistered"
    return registry[key]["status"]   # 'enrolled' or 'revoked'


# ── Audit Log (audit_log.csv) ─────────────────────────────────────────────────

def _append_audit(customer: str, agent: str, action: str,
                  amount: float, decision: str, rule: int) -> None:
    """
    Append one row to audit_log.csv.
    Creates the file with a header row if it doesn't exist yet.
    """
    file_exists = os.path.exists(AUDIT_FILE)
    with open(AUDIT_FILE, "a", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=_AUDIT_COLS)
        if not file_exists:
            writer.writeheader()      # write column names on first use
        writer.writerow({
            "timestamp": _now(),
            "customer":  customer,
            "agent":     agent,
            "action":    action,
            "amount":    int(amount) if amount else "",
            "decision":  decision,
            "rule":      rule,
        })


def cmd_log() -> None:
    """
    Print the audit log as a readable table.
    Shows a friendly message if no decisions have been recorded yet.
    """
    if not os.path.exists(AUDIT_FILE):
        print("  No audit entries yet.")
        return

    with open(AUDIT_FILE, newline="", encoding="utf-8") as fh:
        rows = list(csv.DictReader(fh))

    if not rows:
        print("  Audit log is empty.")
        return

    # Column widths (minimum = header width)
    widths = {col: len(col) for col in _AUDIT_COLS}
    for row in rows:
        for col in _AUDIT_COLS:
            widths[col] = max(widths[col], len(str(row.get(col, ""))))

    def _fmt(row: dict) -> str:
        return "  " + "  ".join(
            str(row.get(col, "")).ljust(widths[col]) for col in _AUDIT_COLS
        )

    header = {col: col for col in _AUDIT_COLS}
    sep    = {col: "-" * widths[col] for col in _AUDIT_COLS}

    print()
    print(_fmt(header))
    print(_fmt(sep))
    for row in rows:
        print(_fmt(row))
    print(f"\n  {len(rows)} record(s) in {AUDIT_FILE}")


def cmd_agents() -> None:
    """Print every entry in agents.json as a readable table."""
    registry = _load_agents()
    if not registry:
        print("  No agents registered yet.")
        return

    print()
    rows = list(registry.values())
    cols = ["customer", "agent", "status", "enrolled_at", "revoked_at"]
    widths = {col: len(col) for col in cols}
    for row in rows:
        for col in cols:
            widths[col] = max(widths[col], len(str(row.get(col, ""))))

    def _fmt(row: dict) -> str:
        return "  " + "  ".join(
            str(row.get(col, "")).ljust(widths[col]) for col in cols
        )

    header = {col: col for col in cols}
    sep    = {col: "-" * widths[col] for col in cols}
    print(_fmt(header))
    print(_fmt(sep))
    for row in rows:
        print(_fmt(row))
    print(f"\n  {len(rows)} agent(s) in {AGENTS_FILE}")


# ── Decision Engine ───────────────────────────────────────────────────────────

def decide(agent_status: str, action: str, amount: float = 0) -> dict:
    """
    Evaluate one agent request against the 7 gatekeeper rules (in order).
    The caller passes the status string looked up from agents.json.

    Parameters
    ----------
    agent_status : 'enrolled' | 'revoked' | 'unregistered'
    action       : 'view_order' | 'place_order' | 'return' | 'refund'
    amount       : Rs value; required (> 0) for place_order and refund

    Returns
    -------
    dict  –  {decision: str, rule: int, reason: str}
    """

    # ── Rule 1 ────────────────────────────────────────────────────────────────
    # A request is "bad" when the action is not recognised at all, OR when the
    # action requires an amount but none (or zero) was provided.
    if action not in VALID_ACTIONS or (action in AMOUNT_REQUIRED and amount <= 0):
        return {
            "decision": "BLOCK",
            "rule": 1,
            "reason": (
                f"Bad request – action '{action}' is unknown or amount is "
                "missing / zero for an action that requires it."
            ),
        }

    # ── Rule 2 ────────────────────────────────────────────────────────────────
    # The agent must have been explicitly registered by this customer.
    # 'unregistered' means no entry exists in agents.json for this pair.
    if agent_status == "unregistered":
        return {
            "decision": "BLOCK",
            "rule": 2,
            "reason": "Agent was never registered by this customer.",
        }

    # ── Rule 3 ────────────────────────────────────────────────────────────────
    # A revoked agent loses ALL access, even for harmless read-only actions.
    if agent_status == "revoked":
        return {
            "decision": "BLOCK",
            "rule": 3,
            "reason": "Agent has been revoked – access denied for all actions.",
        }

    # From this point the agent is confirmed 'enrolled'.

    # ── Rule 4 ────────────────────────────────────────────────────────────────
    # Viewing an order is purely informational; no money moves, so it is always
    # safe to allow without asking the customer.
    if action == "view_order":
        return {
            "decision": "ALLOW",
            "rule": 4,
            "reason": "Viewing an order is a safe, read-only action – allowed.",
        }

    # ── Rule 5 ────────────────────────────────────────────────────────────────
    # A return involves physically shipping goods back and can be complicated to
    # reverse, so the customer must always confirm it explicitly.
    if action == "return":
        return {
            "decision": "ASK CUSTOMER",
            "rule": 5,
            "reason": "Returns require explicit customer confirmation.",
        }

    # ── Rules 6 & 7 ───────────────────────────────────────────────────────────
    # Only 'place_order' and 'refund' reach here (Rule 1 blocked everything
    # else).
    #
    # Rule 6 – Amount exceeds the Rs 5,000 limit → escalate to customer.
    # Rule 7 – Amount is within the limit → agent may act autonomously.
    if amount > LIMIT:
        return {
            "decision": "ASK CUSTOMER",
            "rule": 6,
            "reason": (
                f"Amount Rs {amount:,.0f} exceeds the Rs {LIMIT:,} limit "
                "– customer confirmation required."
            ),
        }
    else:
        return {
            "decision": "ALLOW",
            "rule": 7,
            "reason": (
                f"Amount Rs {amount:,.0f} is within the Rs {LIMIT:,} limit "
                "– allowed autonomously."
            ),
        }


def cmd_decide(customer: str, agent: str, action: str, amount: float) -> None:
    """
    Look up the agent's stored status, run the 7 rules, print the result,
    and append a row to audit_log.csv.
    """
    # Resolve status from agents.json (Rules 2 & 3 depend on this)
    agent_status = _lookup_agent_status(customer, agent)

    result = decide(agent_status, action, amount)

    # ── Persist to audit log ──────────────────────────────────────────────────
    _append_audit(customer, agent, action, amount,
                  result["decision"], result["rule"])

    # ── Print result ──────────────────────────────────────────────────────────
    print(f"\n  Customer     : {customer}")
    print(f"  Agent        : {agent}  [{agent_status}]")
    print(f"  Action       : {action}")
    if action in AMOUNT_REQUIRED:
        print(f"  Amount       : Rs {amount:,.0f}")
    print()
    print(f"  ► Decision   : {result['decision']}")
    print(f"    Rule       : #{result['rule']}")
    print(f"    Reason     : {result['reason']}")
    print()


# ── Helpers ───────────────────────────────────────────────────────────────────

def _now() -> str:
    """Return the current local date-time as an ISO-8601 string (no microseconds)."""
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def _banner() -> None:
    print("=" * 60)
    print("  Nykaa Agent Gatekeeper")
    print(f"  Enrolment : {ENROLMENT}")
    print(f"  Limit     : Rs {LIMIT:,}")
    print("=" * 60)


def _usage_and_exit() -> None:
    print(
        "\nSub-commands:\n"
        "  register <customer> <agent>\n"
        "  revoke   <customer> <agent>\n"
        "  decide   <customer> <agent> <action> [amount]\n"
        "  log\n"
        "  agents\n\n"
        "Actions for decide:\n"
        "  view_order | place_order | return | refund\n"
        "  (place_order and refund require a positive amount in Rs)\n\n"
        "Examples:\n"
        "  python gatekeeper.py register cust_01 agent_A\n"
        "  python gatekeeper.py decide   cust_01 agent_A view_order\n"
        "  python gatekeeper.py decide   cust_01 agent_A place_order 3000\n"
        "  python gatekeeper.py decide   cust_01 agent_A place_order 7000\n"
        "  python gatekeeper.py decide   cust_01 agent_A return\n"
        "  python gatekeeper.py decide   cust_01 agent_A refund 4999\n"
        "  python gatekeeper.py revoke   cust_01 agent_A\n"
        "  python gatekeeper.py decide   cust_01 agent_A view_order\n"
        "  python gatekeeper.py log\n"
        "  python gatekeeper.py agents\n"
    )
    sys.exit(1)


# ── Entry Point ───────────────────────────────────────────────────────────────

def main() -> None:
    _banner()
    args = sys.argv[1:]

    if not args:
        _usage_and_exit()

    sub = args[0].lower()

    # ── register ──────────────────────────────────────────────────────────────
    if sub == "register":
        if len(args) < 3:
            print("  Usage: register <customer> <agent>")
            sys.exit(1)
        cmd_register(customer=args[1], agent=args[2])

    # ── revoke ────────────────────────────────────────────────────────────────
    elif sub == "revoke":
        if len(args) < 3:
            print("  Usage: revoke <customer> <agent>")
            sys.exit(1)
        cmd_revoke(customer=args[1], agent=args[2])

    # ── decide ────────────────────────────────────────────────────────────────
    elif sub == "decide":
        if len(args) < 4:
            print("  Usage: decide <customer> <agent> <action> [amount]")
            sys.exit(1)

        customer = args[1]
        agent    = args[2]
        action   = args[3]
        amount   = 0.0

        if len(args) >= 5:
            try:
                amount = float(args[4])
            except ValueError:
                print(f"  [ERROR] Amount must be a number, got: '{args[4]}'")
                sys.exit(1)

        cmd_decide(customer, agent, action, amount)

    # ── log ───────────────────────────────────────────────────────────────────
    elif sub == "log":
        cmd_log()

    # ── agents ────────────────────────────────────────────────────────────────
    elif sub == "agents":
        cmd_agents()

    else:
        print(f"  [ERROR] Unknown sub-command: '{sub}'")
        _usage_and_exit()


if __name__ == "__main__":
    main()
