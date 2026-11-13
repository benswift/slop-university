# Canon rungs

## 2B. Refine a researcher bio

Rewrite the thin `bio` of the chosen `canon/roster.yml` researcher into a proper
2-3 sentence profile in the institutional register (`skills/from-preset/`
`genre.md`): what they research, the framing their school favours, the unit or
agenda they anchor. No verifiable claims; no invented collaborators outside the
canon; keep their `id`, `name`, `title`, `school`, and `headshot` untouched.

**Files:** `canon/roster.yml`.

## 2C. Flesh out a school / unit / lab blurb

Add or rewrite the `blurb` of the chosen `canon/schools.yml` entry --- one or
two sentences that read straight, in the naming register `canon/schools.md`
describes (a vague noun in a load-bearing position; nothing that winks). Keep
its `id`, `name`, `kind`, and any `school`/`acronym` fields untouched.

**Files:** `canon/schools.yml`.

## 2D. Grow a page

Deepen an existing site page whose content is thin --- typically
`website/src/content/pages/about.md`, or a new institutional page under
`website/src/content/pages/`. Institutional register; no visible satire signal;
no verifiable claims; link only to pages that exist. **Never touch
`colophon.md`** --- it is the one out-of-fiction page and the wrapper resets any
commit that edits it. **Never touch `girt.md`** either --- the ranking-index
table is human-maintained (see the ranking-claim carve-out in
`website/AGENTS.md`) --- nor `sustainability.md`, the out-of-fiction
sustainability report, which the wrapper also resets.

**Files:** a file under `website/src/content/pages/` (not `colophon.md`).

## 2E. Add a researcher (heavy --- rare)

Follow the roster's own admission procedure (the header of `canon/roster.yml`
and the repo `AGENTS.md`), in order:

1. Invent a name that fits the roster's register.
2. **Name-collision check (hard):** web search the full name, including the ANU
   staff directory; no real staff member, notable researcher, or public figure
   may share it. If it collides, pick another name.
3. Generate a house-style headshot per `skills/_shared/visual-style.md` into
   `canon/headshots/<id>.jpg` (the image workflow; steered by
   `references/slop-style/`), and eyeball it for accidental real-person
   likeness.
4. Generate their landscape person hero per the "Person heroes" section of
   `skills/_shared/visual-style.md` into `canon/heroes/people/<id>.avif` (16:9,
   2K; the new headshot as the lead reference, scene themed to their research
   focus), and eyeball it for style compliance (two inks, no baked-in text, no
   recognisable real place).
5. Append the entry to the end of `canon/roster.yml` (`id`, `name`, `title`,
   `school` from `canon/schools.yml`, `email` --- the id with its hyphen(s)
   replaced by dots at slop.university, per the roster header's rule --- a 2-3
   sentence `bio`, `headshot`, `collisionChecked` --- today's date, quoted).
   Touch nothing else in the file, its header included: another run may be
   admitting someone at the same moment, and two appends merge where two edits
   to a shared line do not.

If the collision check is inconclusive, or the headshot or hero can't be
generated, abort the run rather than admit a shaky entry.

When the action names a `school`, the researcher is appointed to it: their field
is the school's, and their bio is a career in that field.

**Files:** `canon/roster.yml`, `canon/headshots/<id>.jpg`,
`canon/heroes/people/<id>.avif`.

## 2F. Add an org unit (rare)

Follow `canon/schools.md`'s admission procedure: name-collision check (no real
school/institute/lab/program may share the name), keep the naming register, then
add the record to the right section of `canon/schools.yml` (`labs`, `programs`,
`initiatives`, etc.) with a unique `id`, a `name`, a `blurb`, and the parent
`school:` id.

**Files:** `canon/schools.yml`.

## 2S. Found a school (about monthly)

The University grows by about one school a month, each in a field of scholarship
no existing school covers, so that its people come to range across the academy.
The action names the existing schools.

1. Choose the field: a broad discipline or family of disciplines none of the
   existing schools' blurbs covers --- somewhere in the humanities, law, the
   natural sciences, mathematics, the arts or the professions.
2. Name the school per `canon/schools.md` and run its **name-collision check
   (hard)**. If it collides, pick another name.
3. Generate its landscape hero into `canon/heroes/schools/<id>.avif` (16:9, 2K,
   house style per `skills/_shared/visual-style.md`; a scene of the school's
   work, no baked-in text, no recognisable real place).
4. Append the record to the `schools:` section of `canon/schools.yml`: `id`,
   `name`, a two-sentence `blurb` saying plainly what the school studies and
   how, and `founded:` (today's date, ISO).

The school arrives empty. Later ticks give it a lab (2F) and its first
researchers (2E); do neither here.

If the collision check is inconclusive or the hero can't be generated, abort the
run rather than found a shaky school.

**Files:** `canon/schools.yml`, `canon/heroes/schools/<id>.avif`.
