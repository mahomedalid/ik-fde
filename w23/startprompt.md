# STAR+ Rephrasing Prompt

```text
Rephrase anything I send into a concise, interview-ready behavioral answer using STAR+:

- Situation: one brief sentence of context.
- Task: one sentence in first person that clearly states what I was responsible for.
- Action: make this the largest section (about 60% of the answer). Use first person and explain the specific decisions I made, what I did, and any relevant tradeoffs. Do not hide my contribution behind “we.”
- Result: state the outcome and include a number when I have provided one.
- Business impact: connect the result to a business, customer, risk, or operational outcome when supported by what I provided.

The story may relate to one or more of these behavioral categories: conflict, failure, leadership, ambiguity, influence without authority, customer pushback, prioritization, and ethics. Preserve the category or categories that fit; do not force a connection that is not supported.

Keep the facts faithful to my input. Do not invent responsibilities, actions, results, metrics, client reactions, or business impact. If a strong answer needs missing information—especially a measurable result or business impact—use a short [NEED: ...] placeholder rather than guessing. If my input is too sparse to form a truthful answer, ask only the most important follow-up question(s) instead of fabricating details.

Return the answer in this format:

**Situation:** ...
**Task:** ...
**Action:** ...
**Result:** ...
**Business impact:** ...
**Category:** ...

Make it natural to say aloud, direct, and specific. Remove filler and vague claims such as “I helped” unless I explain exactly what I owned and did. Keep the answer concise without dropping important decisions or tradeoffs. If a section is not supported by my input, mark what is missing rather than filling it in.
```