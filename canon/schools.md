# The institutional canon: schools and units (doctrine)

The canonical list of schools, units, labs, programs, and named initiatives ---
the persistent org chart of Slop University --- is the structured data in the
sibling [`schools.yml`](schools.yml). The website's `schools` content collection
loads that file directly, and every generated artefact, press release, and site
page draws its org names from it.

This file is the **authoring doctrine**: the rules for growing the institution.
Never invent a new org unit inside a run; add it to `schools.yml` first, subject
to the rules below.

## How to add an org unit

- Run a name-collision check first: no real university school, institute, lab,
  or program may share the name (web search the full name).
- Add the record to the right section of `schools.yml` (`schools`, `units`,
  `labs`, `programs`, `initiatives`, or `history`) with a unique `id` (the URL
  slug), a `name`, and --- for labs, programs, and initiatives --- the parent
  `school:` id.
- Keep the naming register (below).

## Naming register

School and unit names put a vague noun in a load-bearing position and read
straight at a glance ("Emergent Priorities", "Continuous Improvement"). The
close read is where they land. Avoid names that wink (nothing with "slop",
"fake", "synergy"), and avoid names that collide with real institutions.

## Structure

Schools sit directly under the University --- Slop University has no faculties
or colleges. Don't invent one.

The **Office of Research Outputs** is a university-level unit, not a school:
roster researchers are never affiliated to it. It is the producing unit credited
on every research poster and paper.

The in-house terminology detail for the School of Continuous Improvement's
programs and initiatives lives in the impact-report blueprint's Terminology
section; the canonical names are in `schools.yml`.
