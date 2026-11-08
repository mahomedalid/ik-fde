# Week 22 — Decomposition & Case-Study Interviews

## Post-class material

The assignment for this week and everything you need to complete it before the next session.


---

# Part 1 — The assignment and the case prompts

## Week 22 — Case prompts and the take-home

### The assignment

1. Two completed **case write-ups**, in two *different* industries, from the prompts below. Each write-up follows the same spine you used in class: clarify → decompose → scope a 4-week pilot with one `[metric][threshold][population]` success criterion → survive one pushback. Self-score with Part 2 of this document.
2. One **recorded mock decomposition**: 15 minutes, you or a peer pod, with rubric feedback attached.
3. Bring to Week 23: your `DECISIONS.md` and your Week 14 security questionnaire answers. Both come back as interview rounds.

### The prompts

Each is deliberately under-specified. That is the exercise.

**Healthcare**

- H-1 — "Our ER patients wait too long to be seen."
- H-2 — "Build us something to reduce no-show appointments."
- H-3 — "Our clinical documentation takes physicians too long."

**Retail**

- R-1 — "Our online returns are too expensive."
- R-2 — "We want a chatbot for customer support."
- R-3 — "Our demand forecasts are wrong and we're overstocked."

**Manufacturing**

- M-1 — "We have too much unplanned downtime on the line."
- M-2 — "Our quality inspection misses defects."

**Logistics**

- L-1 — "Our delivery promises keep slipping."
- L-2 — "We spend too much on warehouse labor."

**Fintech**

- F-1 — "Too many fraud false positives are blocking real customers."
- F-2 — "We want to automate parts of our loan underwriting."


---

# Part 2 — Scoring rubrics

## Week 22 — Scoring Rubrics (screen-shareable; students grade with these)

Three rubrics: **Decomposition case**, **System-design pushback**, **AI pair-coding**. Each line scores 1–4. A "pass the round" bar is noted under each. Students use these to grade each other live and to self-score the take-home write-ups.

> Print philosophy: keep it on one screen. The point of giving students the rubric is that **knowing exactly what's scored is half of passing.** Real interviewers score on roughly this; we're just making it visible.

---

### Rubric A — Decomposition / Case Round

| Dimension | 1 — Fail | 2 — Weak | 3 — Solid | 4 — Strong |
|---|---|---|---|---|
| **Clarify** | Jumps straight to a solution | Asks 1–2 generic questions | Pins the vague words to a population + a comparison target | Pins metric, population, target *and* surfaces a hidden segmentation before decomposing |
| **Decompose** | No structure; a list of ideas | Partial funnel, gaps | Clean funnel/pipeline that could locate the problem | Funnel + explicitly *locates the dominant segment* with reasoning |
| **Scope (eval anchor)** | No success criterion | Vague ("make it faster") | A real `[metric][threshold][population]` | Criterion is scoped to a 4-week pilot, tied to the located segment, testable on day one |
| **Communication** | "We" throughout; rambling | Mostly "we"; some narration | First-person, narrates reasoning | Narrates *why* at each step; interviewer never has to ask "why" |
| **Pushback survival** | Abandons frame at first objection | Wobbles, partial recovery | Absorbs objection, adjusts a parameter | Absorbs it and uses it to *sharpen* the scope without losing structure |

**Pass bar:** ≥3 on Clarify, Decompose, and Scope; ≥2 on the rest. **The auto-fail:** a 1 on Clarify (panic-solve) caps the whole round at "no hire" regardless of the rest — exactly how real interviewers treat it.

---

### Rubric B — System-Design Pushback (defending your capstone)

| Dimension | 1 — Fail | 2 — Weak | 3 — Solid | 4 — Strong |
|---|---|---|---|---|
| **Trust-boundary reasoning** | Puts security in the LLM, or can't say where it lives | Knows RBAC exists but not why it's below the agent | Correctly places enforcement below the non-deterministic LLM | Explains it from the W16 two-analyst test, layer by layer |
| **Eval / reliability** | "It worked in testing" | Mentions evals vaguely | Names the gate, threshold, smoke vs golden | Ties to continuous eval + adversarial set + the incident they fixed |
| **Cost / scale awareness** | No idea where cost lives | Hand-waves "optimize" | Names model routing / caching as the lever | Quantifies cost per resolution + names what breaks at 10×/multi-tenant |
| **Doesn't fold** | Caves on first pushback | Defends weakly | Holds the frame, concedes only what's true | Turns pushback into a sharper answer; concedes precisely, defends the rest |

**Pass bar:** ≥3 on Trust-boundary and Doesn't-fold (these are the two real interviewers weight hardest for forward-deployed roles).

---

### Rubric C — AI Pair-Coding Round

The interviewer is scoring **how you direct and verify the AI**, not raw coding speed.

| Dimension | 1 — Fail | 2 — Weak | 3 — Solid | 4 — Strong |
|---|---|---|---|---|
| **Direction** | "Write the function" and waits | Vague prompts, lets AI guess | Gives the AI the constraints + edge cases up front | Decomposes the task for the AI, states intent + the data quirks before it can guess wrong |
| **Verification** | Accepts AI output unchecked | Eyeballs it | Runs it, checks the obvious case | Writes/asks for a test first; checks edge cases; catches a wrong assumption |
| **Catching errors** | Misses the AI's bad assumption | Catches it after it breaks | Catches it on review | Pre-empts it ("the date is dd/mm not ISO") so it never happens |
| **Communication** | Silent | Narrates a little | Explains what they're asking and why | Treats the AI like a junior pair — clear intent, reviews like a senior |

**Pass bar:** ≥3 on Direction and Verification. **The tell interviewers love:** the candidate caught the AI being confidently wrong and corrected it *before* running. That's the whole signal.
