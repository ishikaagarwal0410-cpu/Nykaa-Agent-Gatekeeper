# Agent Gatekeeper Rules: Nykaa (Enrolment PGD202564619)

Rules are checked from top to bottom. The first rule that matches decides.

1. Bad request (unknown action, or order/refund with missing or zero amount) -> BLOCK
2. Agent was never registered by this customer -> BLOCK
3. Agent has been revoked -> BLOCK (even for harmless actions)
4. View order -> ALLOW
5. Return -> ASK CUSTOMER
6. Place order or refund above Rs 5,000 -> ASK CUSTOMER
7. Place order or refund up to Rs 5,000 -> ALLOW

Why Rs 5,000? Nykaa's average order is about Rs 2,000, so Rs 5,000 is roughly 2.5 times
a normal basket. Everyday shopping goes through, while unusually large orders get a human check.