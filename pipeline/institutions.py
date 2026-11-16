"""The approved institution list (phase 1, 2026-11-15). Single source of truth.

Each reported institution has a short key, a display name, and one or more
OpenAlex IDs. A work counts for the institution if any author lists one of
those IDs or a sub-unit of them (OpenAlex lineage). UConn Health is not in
UConn's OpenAlex lineage, so UConn lists both IDs (see DECISIONS.md).
"""
INSTITUTIONS = [
    # key, display name, OpenAlex IDs, sector
    ("yale", "Yale University", ["I32971472"], "private"),
    ("uconn", "University of Connecticut (incl. UConn Health)", ["I140172145", "I75929689"], "public"),
    ("wesleyan", "Wesleyan University", ["I100538780"], "private"),
    ("trinity", "Trinity College", ["I56722557"], "private"),
    ("conncoll", "Connecticut College", ["I4498119"], "private"),
    ("quinnipiac", "Quinnipiac University", ["I43267033"], "private"),
    ("fairfield", "Fairfield University", ["I126350171"], "private"),
    ("sacredheart", "Sacred Heart University", ["I130186095"], "private"),
    ("hartford", "University of Hartford", ["I162281398"], "private"),
    ("newhaven", "University of New Haven", ["I40253897"], "private"),
    ("scsu", "Southern Connecticut State University", ["I35462925"], "public"),
    ("ccsu", "Central Connecticut State University", ["I154264771"], "public"),
    ("wcsu", "Western Connecticut State University", ["I204366597"], "public"),
    ("ecsu", "Eastern Connecticut State University", ["I203331390"], "public"),
    ("uscga", "United States Coast Guard Academy", ["I186274478"], "federal"),
    ("bridgeport", "University of Bridgeport", ["I154300980"], "private"),
    ("usj", "University of Saint Joseph", ["I192633058"], "private"),
]

ID_TO_KEY = {oid: key for key, _, ids, _ in INSTITUTIONS for oid in ids}
ALL_IDS = list(ID_TO_KEY)
NAMES = {key: name for key, name, _, _ in INSTITUTIONS}
