# Inbox

This is where I drop rough notes about decisions in my own work. CompEdge, Nayrix, the eval work, the analytics projects, anything where a real call got made.

Every Thursday the daily run picks the oldest note in here and turns it into a proper decision record in `content/decisions`. Once it is used, the note moves to `journal/used`.

## Why this exists

The automation knows nothing about my companies. If I let it write about CompEdge on its own it would invent details, and invented details about my own work is the worst thing this repo could contain. So the rule is simple: it can only use what is in the note. Where the note is thin, it has to put a question in the open questions section instead of filling the gap.

That means the quality of the Thursday piece is entirely down to how honest the note is. Ten rough bullet points with real numbers beat a polished paragraph with none.

## How to write one

Do not make it neat. Bullet points, half sentences, voice-to-text, whatever is fast. Name the file after the decision, like `compedge-pricing-tiers.md` or `nayrix-hiring-first-engineer.md`.

Cover these, roughly:

- What was the decision. Not the project, the decision.
- What were the options I actually considered. Including the one I rejected early.
- What did I know at the time, and what was I guessing.
- What did I pick and why.
- What happened after. If it is too early to tell, say so.
- What I would do differently.

Numbers matter more than adjectives. "Pricing went from X to Y and conversion did Z" is worth more than "pricing was a challenge". If I cannot share a real number publicly, say so in the note and the record will use a ratio or a range instead.

If a note contains something confidential, say so at the top with a line starting `CONFIDENTIAL:` and name what cannot go public. The run will work around it rather than publishing it.

## Files starting with an underscore are ignored

`_template.md` sits here as a starting point and never gets picked up.
