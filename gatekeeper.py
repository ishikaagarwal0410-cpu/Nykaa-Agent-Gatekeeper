"""
gatekeeper.py – Nykaa Agent Gatekeeper
Enrolment: PGD202564619

Implements the 7-rule decision engine from RULES.md.
Rules are evaluated strictly top-to-bottom; the first match wins.

Usage:
    python gatekeeper.py <agent_status> <action> [amount]

    agent_status : enrolled | revoked | unknown
    action       : view_order | place_order | return | refund
    amount       : required for place_order / refund (integer, in Rs)

Examples:
    python gatekeeper.py enrolled  view_order
    python gatekeeper.py enrolled  place_order 3000
    python gatekeeper.py enrolled  place_order 7000
    python gatekeeper.py revoked   place_order 500
    python gatekeeper.py unknown   view_order
    python gatekeeper.py enrolled  return
    python gatekeeper.py enrolled  refund 4999
"""

import sys

# ── Configuration ─────────────────────────────────────────────────────────────

ENROLMENT = "PGD202564619"

# Rule 6 / 7 threshold: orders/refunds above this amount need a human check.
# Nykaa's average order is ~Rs 2,000; Rs 5,000 ≈ 2.5× a normal basket.
LIMIT = 5_000  # Rs

# Valid actions recognised by the gatekeeper
VALID_ACTIONS = {"view_order", "place_order", "return", "refund"}

# Actions that MUST carry a non-zero amount
AMOUNT_REQUIRED = {"place_order", "refund"}

# ── Decision Engine ───────────────────────────────────────────────────────────

def decide(agent_status: str, action: str, amount: float = 0) -> dict:
    """
    Evaluate one agent request against the 7 gatekeeper rules (in order).

    Parameters
    ----------
    agent_status : str
        Registration state of the agent: 'enrolled', 'revoked', or anything
        else (treated as never-registered / unknown).
    action : str
        Requested operation: 'view_order', 'place_order', 'return', 'refund'.
    amount : float, optional
        Transaction value in Rs. Required (and must be > 0) for 'place_order'
        and 'refund'. Ignored for 'view_order' and 'return'.

    Returns
    -------
    dict with keys:
        decision  – 'ALLOW', 'ASK CUSTOMER', or 'BLOCK'
        rule      – rule number that matched (1-7)
        reason    – short human-readable explanation
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
    # The agent must have been explicitly enrolled by the customer.  Any status
    # other than 'enrolled' or 'revoked' means the agent was never registered.
    if agent_status not in ("enrolled", "revoked"):
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
    # Only 'place_order' and 'refund' reach here (Rule 1 already blocked any
    # other action that isn't in VALID_ACTIONS).
    #
    # Rule 6 – Amount exceeds the Rs 5,000 limit → escalate to customer.
    # Rule 7 – Amount is within the limit → allow autonomously.
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


# ── Command-Line Interface ────────────────────────────────────────────────────

def _banner() -> None:
    print("=" * 60)
    print("  Nykaa Agent Gatekeeper")
    print(f"  Enrolment: {ENROLMENT}")
    print(f"  Limit    : Rs {LIMIT:,}")
    print("=" * 60)


def _usage_and_exit() -> None:
    print(
        "\nUsage:\n"
        "  python gatekeeper.py <agent_status> <action> [amount]\n\n"
        "  agent_status : enrolled | revoked | <anything-else>\n"
        "  action       : view_order | place_order | return | refund\n"
        "  amount       : required for place_order / refund (Rs, integer)\n\n"
        "Examples:\n"
        "  python gatekeeper.py enrolled  view_order\n"
        "  python gatekeeper.py enrolled  place_order 3000\n"
        "  python gatekeeper.py enrolled  place_order 7000\n"
        "  python gatekeeper.py enrolled  return\n"
        "  python gatekeeper.py enrolled  refund 4999\n"
        "  python gatekeeper.py revoked   place_order 500\n"
        "  python gatekeeper.py unknown   view_order\n"
    )
    sys.exit(1)


def main() -> None:
    _banner()

    args = sys.argv[1:]
    if len(args) < 2:
        _usage_and_exit()

    agent_status = args[0]
    action = args[1]

    amount = 0.0
    if len(args) >= 3:
        try:
            amount = float(args[2])
        except ValueError:
            print(f"[ERROR] Amount must be a number, got: '{args[2]}'")
            _usage_and_exit()

    result = decide(agent_status, action, amount)

    print(f"\n  Agent status : {agent_status}")
    print(f"  Action       : {action}")
    if action in AMOUNT_REQUIRED:
        print(f"  Amount       : Rs {amount:,.0f}")
    print()
    print(f"  ► Decision   : {result['decision']}")
    print(f"    Rule       : #{result['rule']}")
    print(f"    Reason     : {result['reason']}")
    print()


if __name__ == "__main__":
    main()
