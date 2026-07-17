# Genre and steering doctrine (preset-driven satire)

Cross-cutting doctrine for the preset-driven satirical-document path
(`skills/from-preset/SKILL.md` and the blueprints in
`skills/from-preset/presets/`). Presets add document-specific structural shape
and reservoirs but defer to this file for the steering rule.

This file is **not** loaded by `skills/from-source/SKILL.md`: the faithful path
doesn't apply institutional voice to its input. If you find yourself wanting to
apply these rules to a from-source run, that's a sign you should be running a
preset instead.

## The genre's defining language moves

These are the voice the joke depends on. Reproduce them straight; do not
editorialise.

- **The preset's declared register, held throughout** --- e.g. future tense ("we
  will") for a strategy, past-tense reflective ("we have") for an impact report,
  academic-present ("results suggest") for a poster or paper. Each blueprint's
  Register row is authoritative; the register is fixed per doc type
- **Vague nouns in load-bearing positions**: capability, ecosystem, trajectory,
  alignment, posture, footprint, fabric, settings
- **Bridging verbs**: enable, catalyse, underpin, anchor, amplify, mobilise,
  harmonise, lean into
- **Transformations between adjacent abstractions**: "from disconnected effort
  to coherent action", "from reactive to anticipatory", "from siloed expertise
  to networked capability"
- **Noun stacks**: "research-education-engagement nexus",
  "knowledge-capability-impact pipeline"
- **Hedging language at the edges**, even when the wrapped claim is unhinged
- **No exclamation marks** (singles, very sparingly, only in genuine rhetorical
  use)
- **No first-person passion, exhortation, or activist verbs** ("fight",
  "resist", "demand", "rise up")
- **No manifesto / rant / press-release register**

## Steering

The steering prompt IS the document's topic. The genre voice (the language moves
above) is the only floor; everything else opens up.

The joke is the contrast: institutional voice articulating unhinged content. The
reader knows immediately what the prompt was; the pleasure is watching the
institution's voice keep wrapping the absurd in vague nouns, bridging verbs, and
transformations between adjacent abstractions. Hedging language at the edges,
specific falsifiable commitments at the centre.

The institution's gaze is the constant; the setting is not. Objects and themes
range across everyday life --- households, shops, streets, transit, workplaces,
playgrounds --- with the campus one setting among many. The satire is an
institution applying total rigour to the ordinary, and the ordinary belongs to
everyone; a corpus that only ever studies its own campus narrows the joke to
people who live there.

## Voice is the floor

The genre voice (the "language moves" list above) is preserved without exception
--- every move on that list holds even when the wrapped claim is unhinged. The
steering prompt opens up content, never register.

## Voice-preserving commitment shapes

Shapes that read as institutional voice wrapping a specific commitment. Use
these as a menu throughout the document --- not gated to one slot.

- A target that's too round and too specific ("100% of X by Y date with no
  exception sustained for more than a single review cycle")
- A pull-quote that names a falsifiable structural claim
- A metric that's too clean ("100% of SES participants reported behaviour change
  at 6-month follow-up")
- A chart annotation labelling an outlier with a checkable date and figure
- An initiative that commits to a published, audited list with no override
  mechanism

These all stay in genre voice --- still institutional, still hedging at the
edges --- while committing to something specific, structural, and checkable that
real documents avoid.

### Worked examples (strategy)

For "lean into sovereign capability":

- Hedge (real plan): "We will strengthen our contribution to the country's
  strategic capability."
- Voice-preserving unhinged: "By 2031, every flagship research initiative at the
  University will be aligned to a published national strategic priority, with no
  exception sustained for more than a single review cycle."

For "lean into radical transparency":

- Hedge (real plan): "We will continue to strengthen open and accountable
  governance."
- Voice-preserving unhinged: "By 2031, every committee minute, budget line, and
  item of professorial correspondence will be published in full within 24 hours,
  with no redaction mechanism and no exception sustained for more than a single
  review cycle."

For "rise to the AI moment":

- Hedge (real plan): "We will deepen our engagement with artificial intelligence
  across research and education."
- Cranked (McSweeney's-grade): "By 2031, every degree program will require a
  Cybernetic Stewardship attestation, with the School of Continuous Improvement
  serving as the convening authority for a published register of AI-system
  custodianship across the institution."

The cranked version still sits in genre voice (vague nouns: _engagement_,
_Cybernetic Stewardship_, _custodianship_; bridging verbs: _convening_; hedging
at the edges: _across the institution_) while making a structural, falsifiable,
surprising commitment. This register repeats throughout the document rather than
being confined to one slot.

Presets carry doc-specific shapes inline in their own blueprints (charts and
metrics are commitment vectors wherever a preset declares them; the academic
presets specialise the voice into an academic-present register).

## People and attribution (the roster rule)

Any named person in a generated artefact --- author, quoted researcher, foreword
signatory, project lead --- comes from the persistent roster in
`canon/roster.yml`, with their canonical title and school. Never a real person,
never a name invented inside a run. Where a document genuinely shouldn't name
anyone (aggregate acknowledgements, external-partner vignettes), attribution
stays institutional, drawn from `canon/schools.md`. _Reference-list_ citations
are the exception in the other direction: both academic presets cite **real,
verified literature** (the paper's bibliography and the poster's references list
alike --- every entry resolves via DOI or arXiv; see each blueprint), so a cited
work's real authors are the one place outside real names legitimately appear.
Never fabricate a citation.

## Bad steering (voice cracks)

- Document drops out of institutional register into manifesto
- First-person passion or exhortation bleeds in
- Activist verbs replace bridging verbs
- Exclamation marks proliferate
- Reads as someone advocating for the theme rather than the institution
  articulating it
- Wrapping language stops hedging --- direct claims throughout with no
  institutional softening reads as a press release, not a strategic plan or
  impact report

## Good steering (voice survives unhinged content)

- The doc is unmistakably about the prompt at every level --- pillar / area
  names, KPIs, initiatives, foreword, vision, charts
- The institution's voice has been bent to articulate the theme
- Hedging language wraps specific, structural, falsifiable commitments
- A reader who knows the institution feels the dissonance immediately

## Off-limits to steering

Hard infrastructure only --- formula-locked across all runs (per the preset's
blueprint):

- Document title (per preset)
- Period covered (per preset)
- Back cover lockup
- PDF metadata title formula
- Any heading the preset explicitly fixes (e.g. strategy's "Executive summary"
  --- a load-bearing genre convention; or strategy's implementation-phase
  verb-set, abstract by definition)

Everything else is fair game.
