# The comms register (press releases and news posts)

A voice family of its own, distinct from both the booklet corporate-plan voice
and the paper/poster academic voice: **institutional media-release**. It is the
voice of a university media office announcing research it is proud of and does
not entirely understand.

Defers to `../from-preset/genre.md` for the floor (vague nouns, bridging verbs,
hedging at the edges, no exclamation marks, no manifesto register) and to
`canon/roster.yml` / `canon/schools.md` for every name.

## Before writing (hard)

Read the **eight most recent posts** in `website/src/content/news/` and list
their opening sentences, pride formulas, quote frames, and method-paragraph
openers. The new release may reuse **none of them** --- not the sentence, not
the frame. The corpus is the site's most visible surface, and a reader who
notices two releases sharing a quote has caught the machine.

Phrases burnt by past overuse, banned permanently regardless of what the recent
eight contain:

- "Researchers at the School of … have released new findings on …" (as an
  opener)
- "This work opens important conversations about …"
- "We look forward to seeing where the community takes …" (and its "… how the
  sector responds to …" variants)
- "Drawing on N months of …" (as a method-paragraph opener)

Vary the lede itself, not just its words. A release may open with the finding,
with the institutional frame, with a researcher's quote, with the method in
comms-speak, or with the school's agenda --- rotate against the recent eight.

## The genre's moves

- **Headline**: present-tense institutional achievement, no wordplay. "Slop
  University researchers map the drift of institutional enthusiasm" --- not
  clever, just proud. Keep it punchy: one claim, ideally under ~80 characters.
  The trimmed specificity (the setting, the mechanism, the qualifier) goes in
  the deck, not a longer headline.
- **Deck (`subtitle`)**: an optional one-line standfirst under the headline, set
  in the `subtitle` frontmatter field. It carries what the punchy headline drops
  --- the study's setting, the mechanism, or the qualifying clause --- in a
  single line that reads as an elaboration of the head, not a summary of the
  release (that's the `description`, which stays card- and meta-only). No em
  dashes in the frontmatter value. The site renders it as a deck beneath the
  hero, matching the output landing page.
- **Standfirst / opening paragraph**: what was published (or announced), by
  whom, and why it "matters", in one or two sentences. Compose it fresh per
  release --- the "Before writing" check above exists because every past
  exemplar here ended up cloned verbatim.
- **The pride formula**: one per release, varied between runs --- "the
  University is proud to…", "the work reflects the University's ongoing
  commitment to…", "the release marks a significant milestone in…" are the
  _species_, not a menu to copy from; coin the run's own.
- **Roster quotes**: 1-2, attributed with canonical name and title. The quotes
  say **nothing at all**, warmly --- but each release finds its own way of
  saying nothing. Rotate the frame: a quote can gesture at the future, place the
  work in "the University's broader journey", thank an unnamed community,
  reflect on what the school "has learned about itself", or welcome the
  questions the work raises. Never reuse a quote frame from the recent eight,
  and never the banned phrases above.
- **The method paragraph**: one, translating the artefact's content into
  comms-speak --- bridging verbs, noun stacks, no technical detail survives.
- **The availability line**: closes the release. "The full <poster/report/paper>
  is available from the University's research repository under an open licence,
  doi:10.5555/slop.<seed>."

## Hedged-commitment discipline (hard)

Media-release voice loves verifiable numbers, and **every one is forbidden**: no
grant dollars ("$4.2M" → "significant external investment"), no rankings
("ranked first in the region" → "recognised across the sector"), no dated
targets, no partner-organisation names (archetype descriptions only, per the
impact-report doctrine, and rarely needed in a release). Significance is
asserted without a checkable referent. Numbers from _inside the artefact_ (its
n, its effect sizes) may be echoed --- they're part of the fiction --- but
nothing about the institution itself is quantified.

## Rules

- Named people: roster only, canonical name + title, and only researchers
  credited on the output being announced (plus at most one other roster member
  in a "welcoming the work" role).
- No exclamation marks; no "groundbreaking"/"world-first" superlatives
  (verifiable-shaped claims); "novel" and "significant" are the ceiling.
- 150-300 words. A release that runs long starts explaining, and explaining
  breaks the voice.
- Vary structure, pride formula, and quote shapes between runs --- the ledger
  holds previous topics; don't reuse phrasing either.
- Reads straight: no winks, no satire signals. The joke is the genre.
