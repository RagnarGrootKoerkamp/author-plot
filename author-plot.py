#!/usr/bin/env python3

# NOTE: Make sure to do a recursive clone to get biblib.

from pathlib import Path
from matplotlib import pyplot as plt

# Fix broken imports in biblib.
import collections
import collections.abc

collections.Iterable = collections.abc.Iterable

import biblib.bib as bib
import biblib.messages as messages
import biblib.algo as algo

import sys

if len(sys.argv) > 1:
    f = Path(sys.argv[1])
else:
    f = Path("references.bib")


# Return list of [(key, year, month, title, [authors])]
def parse(f):
    f = Path(f).open()
    db = bib.Parser().parse(f).get_entries()
    db = bib.resolve_crossrefs(db)
    recoverer = messages.InputErrorRecoverer()
    l = []
    for ent in db.values():
        with recoverer:
            l.append(parse_entry(ent))
    recoverer.reraise()
    return l


def parse_entry(ent):
    # print(ent)
    key = ent.key
    year = ent["year"]
    # month = ent.month_num() if 'month' in ent else None
    month = None
    title = parse_tex(algo.title_case(ent["title"]))
    authors = [parse_tex(author.pretty()) for author in ent.authors()]
    tup = (key, year, month, title, authors)
    # print(tup)
    return tup


def parse_tex(s):
    try:
        return algo.tex_to_unicode(s)
    except:
        return s


data = parse(f)
data.sort(key=lambda x: x[1])

authors = []
new_data = []
for key, year, month, title, ats in data:
    for a in ats:
        if a not in authors:
            authors.append(a)
            # new_data.append((a, [a]))
    new_data.append((key + " " + year, ats))

# dots
data = new_data
data.reverse()
good = [
    (j, i) for (i, (t, d)) in enumerate(data) for (j, a) in enumerate(authors) if a in d
]
bad = [
    (j, i)
    for (i, (t, d)) in enumerate(data)
    for (j, a) in enumerate(authors)
    if a not in d
]
hlines = [
    (min(authors.index(a) for a in d), max(authors.index(a) for a in d))
    for (t, d) in data
]

scale = 1 / 4
sz = 40
fig, ax = plt.subplots(figsize=(len(authors) * scale, len(data) * scale))

ax.scatter(
    [x for (x, y) in good],
    [y for (x, y) in good],
    s=sz,
    c="black",
    zorder=10,
)
ax.scatter(
    [x for (x, y) in bad],
    [y for (x, y) in bad],
    s=sz,
    c="lightgrey",
    zorder=10,
)
ax.hlines(
    list(range(len(data))),
    [l for (l, r) in hlines],
    [r for (l, r) in hlines],
    colors="black",
    zorder=20,
)
ax.set_frame_on(False)
ax.grid(False)
ax.tick_params(axis="both", which="both", length=0)
ax.yaxis.set_ticks(list(range(len(data))))
ax.yaxis.set_ticklabels([t for (t, d) in data])
ax.xaxis.set_ticks_position("top")
ax.xaxis.set_ticks(list(range(len(authors))))
ax.xaxis.set_ticklabels(authors, rotation=90)

for x in range(0, len(authors), 2):
    rect = plt.Rectangle(
        (x - 0.5, -0.5),
        1,
        len(data),
        facecolor=(0.97, 0.97, 0.97),
        edgecolor=None,
        zorder=0,
    )

    ax.add_patch(rect)

out = f.with_suffix(".svg")
fig.savefig(out, bbox_inches="tight")
