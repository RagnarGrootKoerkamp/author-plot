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

# An optional yaml file with structure:
# - bibkey:
#     tags: [list of tags]
# that specifies the sort order.
meta = f.with_suffix(".yaml")
if meta.is_file():
    # Read the YAML file.
    import yaml

    meta = yaml.safe_load(meta.open())

    # Flatten the meta dictionary.
    flat_meta = dict()
    for i, kv in enumerate(meta):
        assert len(kv) == 1
        for k, v in kv.items():
            if v is None:
                v = dict()
            if "tags" not in v:
                v["tags"] = []
            v["order"] = i
            flat_meta[k] = v
    meta = flat_meta

else:
    meta = None


filter = "--filter" in sys.argv
first = "--first" in sys.argv


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
    if key in meta and "name" in meta[key]:
        title = meta[key]["name"] + " " + year
    else:
        title = key + " " + title + " " + year
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

if meta:
    data.sort(key=lambda x: meta[x[0]]["order"])
print(data)

authors = []
author_cnt = dict()
new_data = []
tags = []

for key, year, month, title, ats in data:
    for a in ats:
        if a not in authors:
            authors.append(a)
            author_cnt[a] = 0
        author_cnt[a] += 1

    # First authors are always kept.
    author_cnt[ats[0]] += 1

    ts = meta[key]["tags"] if meta else []
    new_data.append((title, ats, ts))

    for t in ts:
        if t not in tags:
            tags.append(t)


if filter:
    authors = [a for a in authors if author_cnt[a] > 1]
    for i in range(len(new_data)):
        (val, ats, ts) = new_data[i]
        new_data[i] = (val, [a for a in ats if author_cnt[a] > 1], ts)

# dots
data = new_data
data.reverse()
A = len(authors) + 1
all_dots = [(j, i) for i in range(len(data)) for j in range(len(authors))]
all_dots += [(A + j, i) for i in range(len(data)) for j in range(len(tags))]
author_dots = [
    (j, i)
    for (i, (_, d, _)) in enumerate(data)
    for (j, a) in enumerate(authors)
    if a in d
]
tag_dots = [
    (A + j, i)
    for (i, (_, _, ts)) in enumerate(data)
    for (j, t) in enumerate(tags)
    if t in ts
]
first_author_dots = [
    (j, i)
    for (i, (_, d, _)) in enumerate(data)
    for (j, a) in enumerate(authors)
    if a == d[0]
]

hlines = [
    (i, (min(authors.index(a) for a in d), max(authors.index(a) for a in d)))
    for (i, (t, d, _)) in enumerate(data)
]
hlines += [
    (i, (A + min(tags.index(t) for t in ts), A + max(tags.index(t) for t in ts)))
    for (i, (_, _, ts)) in enumerate(data)
    if ts
]

scale = 1 / 4
sz = 40
first_sz = 12
fig, ax = plt.subplots(figsize=(len(authors) * scale, len(data) * scale))

# Background dots
ax.scatter(
    [x for (x, y) in all_dots],
    [y for (x, y) in all_dots],
    s=sz,
    c="lightgrey",
    zorder=10,
)
# Horizontal paper connection lines
ax.hlines(
    [i for (i, _) in hlines],
    [l for (_, (l, r)) in hlines],
    [r for (_, (l, r)) in hlines],
    colors="black",
    zorder=10,
)
# Author dots
ax.scatter(
    [x for (x, y) in author_dots],
    [y for (x, y) in author_dots],
    s=sz,
    c="black",
    zorder=10,
)
# Tag dots
ax.scatter(
    [x for (x, y) in tag_dots],
    [y for (x, y) in tag_dots],
    s=sz,
    c="black",
    zorder=10,
)
# First author dots
if first:
    ax.scatter(
        [x for (x, y) in first_author_dots],
        [y for (x, y) in first_author_dots],
        s=first_sz,
        c="white",
        zorder=10,
    )
ax.set_frame_on(False)
ax.grid(False)
ax.tick_params(axis="both", which="both", length=0)
ax.yaxis.set_ticks(list(range(len(data))))
ax.yaxis.set_ticklabels([t for (t, d, _) in data])
ax.xaxis.set_ticks_position("top")
ax.xaxis.set_ticks(list(range(len(authors))) + list(range(A, A + len(tags))))
ax.xaxis.set_ticklabels(authors + tags, rotation=90)

# Grey rectangles
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

for x in range(0, len(tags), 2):
    x += A
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
