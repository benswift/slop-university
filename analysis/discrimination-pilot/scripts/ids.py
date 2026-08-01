#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.12"
# dependencies = []
# ///
"""The stimulus item id, defined once.

Item ids are derived from the excerpt's own identity rather than its position in
a sample, so that a judgement stays attached to the excerpt that was judged when
the corpus grows and the sampler re-runs. Three scripts need to agree on the
rule --- `sample_stimuli.py` assigns it, `vagueness.py` scores against it, and
`vagueness_vs_error.py` joins the two --- and a hash rule copied into three
files is exactly the kind of thing that drifts silently and is then very hard to
notice, because a mismatched join looks like a null result rather than an error.
"""

from __future__ import annotations

import hashlib

PREFIX = "E"
WIDTH = 8


def item_id(excerpt_id: str) -> str:
    """Stable id for an excerpt, from its `<source-doc>--<n>` identifier."""
    return PREFIX + hashlib.sha1(excerpt_id.encode()).hexdigest()[:WIDTH]


def doc_key(excerpt_id: str) -> str:
    """The source document an excerpt came from."""
    return excerpt_id.rsplit("--", 1)[0]
