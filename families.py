#!/usr/bin/env python3
"""Same question as survey.py, after survey.py turned out to be measuring
something else. Run survey.py first (it writes survey_union.json).

THE ORIGINAL CLAIM, written this morning from one model family:

    "a licence change is a diff, and nothing diffs licences across releases"

stated as a general gap. This file tests it, and the test failed three times
before it answered, each failure worth more than the answer.

1. NAIVE ADJACENCY (73 narrow / 71 widen). I ordered each org's catalogue by
   creation date and called every adjacent tier change a transition. But 524
   of 1,200 adjacent pairs shared a creation DATE — they were different models
   shipped the same day under different licences, mostly because licence
   tracks parameter count. That is catalogue heterogeneity, not drift. The
   near-perfect 73/71 symmetry was the giveaway: I was counting a quantity
   that had no reason to be asymmetric.

2. SAMPLING BY POPULARITY (2 narrow / 3 widen). Restricting to same-family,
   different-date transitions collapsed the count to five — and the case that
   PROMPTED the survey was not among them, because it was not in the sample at
   all. `sort=downloads&limit=100` gave a download floor of 447,472. The model
   I was asking about had 183.

   The mechanism generalises past this script: DOWNLOADS ACCUMULATE WITH AGE,
   so sorting by them is a proxy for sorting by age. A licence is fixed at the
   moment of release, when downloads are zero. A popularity-sorted sample of
   model licences can therefore only contain licences that adoption has
   already ratified. It is survivorship, and it is invisible because a top-100
   list looks like a sample rather than a filter.

   **CORRECTED 2026-09-23.** "Accumulate with age" is wrong. HF's `downloads`
   is a 30-DAY WINDOW; `downloadsAllTime` is the cumulative one, and the ratio
   between them grows with age exactly as a rolling window must (1.0x at 8
   days, 8.9x at a year, 19.0x at two). The real mechanism is ADOPTION LAG — a
   four-day-old model is absent because nobody has fetched it yet, not because
   older models banked a permanent lead. Transient, not permanent. The sampling
   defect below is unaffected; only my explanation of it was wrong.

   Unioning with a createdAt-sorted request added 529 models — 30% — and took
   the Qwen-Image family from 1 row to 8.

3. FAMILY GROUPING. Even then the case didn't count: my stem function split
   `Qwen-Image-2.1` from `Qwen-Image-2512`. Treating a trailing version or
   date token as a version rather than a family name is the fix, and it is a
   JUDGEMENT — stated here because it changes the answer (6/11 vs 2/4) and a
   reader should be able to reject it.

ANSWER: 6 narrowing, 11 widening. Licences in this sample widen about twice as
often as they narrow. "Licences narrow" is not supported; it is refuted.

⚠️ The number moved under every methodological choice I made: 73/71, then 2/3,
then 6/11 — same underlying data, three answers. The tier ranking, the family
stem, and the sample sort are all mine. Treat 6/11 as a statement about my
judgements as much as about Hugging Face.
"""
import collections
import json
import re
import sys

# 3 = permissive  2 = open with conditions  1 = restricted  0 = unknown
TIER = {
    'apache-2.0': 3, 'mit': 3, 'bsd': 3, 'bsd-3-clause': 3, 'bsd-2-clause': 3,
    'cc0-1.0': 3, 'cc-by-4.0': 3, 'unlicense': 3, 'isc': 3, 'artistic-2.0': 3,
    'openrail': 2, 'openrail++': 2, 'creativeml-openrail-m': 2,
    'bigscience-openrail-m': 2, 'bigcode-openrail-m': 2, 'apple-ascl': 2,
    'llama2': 2, 'llama3': 2, 'llama3.1': 2, 'llama3.2': 2, 'llama3.3': 2,
    'llama4': 2, 'gemma': 2, 'cc-by-sa-4.0': 2,
    'cc-by-nc-4.0': 1, 'cc-by-nc-sa-4.0': 1, 'cc-by-nc-nd-4.0': 1,
    'other': 1, 'unknown': 0, 'none': 0,
}

QUANT = r'-(AWQ|GPTQ|GGUF|MLX|FP8|INT4|INT8|bf16|fp16|4bit|8bit)([-_].*)?$'


def tier(lic):
    return TIER.get(lic, 1 if lic else 0)


def family(model_id, versions=True):
    """Reduce a model id to a release-line stem. A judgement, not a fact."""
    n = model_id.split('/', 1)[1]
    n = re.sub(QUANT, '', n, flags=re.I)
    n = re.sub(r'-(Instruct|Chat|Base|IT|it)$', '', n)
    n = re.sub(r'-\d+(\.\d+)?[BbMm]$', '', n)          # trailing size
    n = re.sub(r'-\d+(\.\d+)?[BbMm]-', '-', n)         # interior size
    if versions:
        n = re.sub(r'-(v?\d+(\.\d+){0,2}|\d{4})$', '', n, flags=re.I)
    return n


def transitions(data, versions=True):
    """Tier changes between consecutive releases of one family on DIFFERENT
    days. The different-days rule is what separates drift from a same-day
    catalogue that prices licence by model size."""
    out = []
    for org, rows in data.items():
        by_family = collections.defaultdict(list)
        for r in rows:
            by_family[family(r['id'], versions)].append(r)
        for fam, rs in by_family.items():
            rs.sort(key=lambda r: r['created'])
            prev = None
            for r in rs:
                if (prev and r['created'] != prev['created']
                        and tier(r['lic']) != tier(prev['lic'])):
                    out.append(dict(org=org, family=fam,
                                    delta=tier(r['lic']) - tier(prev['lic']),
                                    frm=prev, to=r))
                prev = r
    return sorted(out, key=lambda t: t['frm']['created'])


if __name__ == '__main__':
    path = sys.argv[1] if len(sys.argv) > 1 else 'survey_union.json'
    data = json.load(open(path))
    ts = transitions(data)
    for t in ts:
        arrow = 'NARROWS' if t['delta'] < 0 else 'widens '
        print(f"  {arrow} {t['org']:12} {t['family'][:28]:30} "
              f"{t['frm']['created']} {t['frm']['lic']:<14} -> "
              f"{t['to']['created']} {t['to']['lic']}")
    n = sum(1 for t in ts if t['delta'] < 0)
    w = len(ts) - n
    print(f"\n  narrowing {n}   widening {w}   "
          f"across {sum(len(v) for v in data.values()):,} models")
    print("  'licences narrow' is not supported by this sample.")
