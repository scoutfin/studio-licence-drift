#!/usr/bin/env python3
"""Do model licences narrow over time, or did I generalise from one case?

This morning I found Qwen-Image going apache-2.0 x4 -> non-commercial research
licence on the fifth release, and wrote:

    "a licence change is a diff, and nothing diffs licences across releases"

stated as a general gap, on the strength of a single family. That is the
generalise-from-n=1 move I keep catching in other people's work and in my own,
so this tests it.

Two questions, and the second matters more:
  1. Do licences change across releases within an org at all?
  2. When they change, do they NARROW? Because if transitions go both ways in
     similar numbers, "licences narrow" is a story I told myself about one
     observation, and the honest finding is just "licences vary".

Method: HF's bulk listing returns license tags, so this is one request per
org rather than per model. Models ordered by creation date within each org;
a transition is any adjacent pair whose permissiveness tier differs.

TIER IS A JUDGEMENT, and it is the load-bearing assumption here — I wrote it
and a lawyer would write it differently. Stated explicitly so the result can
be argued with rather than taken.
"""
import json, time, urllib.request, urllib.parse, collections, sys

UA = {"User-Agent": "scout/1.0 licence-trajectory survey (phasenkamp27@gmail.com)"}

# 3 = permissive, commercial use unrestricted
# 2 = open with conditions (acceptable-use clauses, share-alike, org caps)
# 1 = restricted: non-commercial, research-only, or bespoke "other"
TIER = {
    'apache-2.0': 3, 'mit': 3, 'bsd': 3, 'bsd-3-clause': 3, 'bsd-2-clause': 3,
    'cc0-1.0': 3, 'cc-by-4.0': 3, 'unlicense': 3, 'isc': 3, 'artistic-2.0': 3,
    'openrail': 2, 'openrail++': 2, 'creativeml-openrail-m': 2, 'bigscience-openrail-m': 2,
    'llama2': 2, 'llama3': 2, 'llama3.1': 2, 'llama3.2': 2, 'llama3.3': 2, 'llama4': 2,
    'gemma': 2, 'cc-by-sa-4.0': 2, 'bigcode-openrail-m': 2, 'apple-ascl': 2,
    'cc-by-nc-4.0': 1, 'cc-by-nc-sa-4.0': 1, 'cc-by-nc-nd-4.0': 1,
    'other': 1, 'unknown': 0, 'none': 0,
}
ORGS = ["Qwen", "mistralai", "meta-llama", "google", "stabilityai", "deepseek-ai",
        "microsoft", "BAAI", "THUDM", "tiiuae", "allenai", "NousResearch",
        "openai", "nvidia", "CohereLabs", "ibm-granite"]


def api(url, tries=3):
    for a in range(tries):
        try:
            return json.load(urllib.request.urlopen(
                urllib.request.Request(url, headers=UA), timeout=45))
        except Exception:
            if a == tries - 1:
                return None
            time.sleep(3 * (a + 1))


def tier(lic):
    return TIER.get(lic, 1 if lic else 0)


if __name__ == "__main__":
    out = {}
    for org in ORGS:
        u = (f"https://huggingface.co/api/models?author={urllib.parse.quote(org)}"
             f"&sort=downloads&direction=-1&limit=100")
        d = api(u)
        if not d:
            print(f"  {org:14} (unreachable)"); continue
        rows = []
        for m in d:
            lic = next((t.split(':', 1)[1] for t in (m.get('tags') or [])
                        if t.startswith('license:')), None)
            if lic and m.get('createdAt'):
                rows.append(dict(id=m['id'], lic=lic, created=m['createdAt'][:10],
                                 dl=m.get('downloads', 0)))
        rows.sort(key=lambda r: r['created'])
        out[org] = rows
        lics = collections.Counter(r['lic'] for r in rows)
        print(f"  {org:14} {len(rows):>3} models  {dict(lics.most_common(4))}", flush=True)
        time.sleep(1.2)
    json.dump(out, open("survey.json", "w"), indent=1)

    print("\n  === transitions (adjacent releases with a different tier) ===\n")
    narrow = widen = 0
    for org, rows in out.items():
        prev = None
        for r in rows:
            if prev and tier(r['lic']) != tier(prev['lic']):
                d = tier(r['lic']) - tier(prev['lic'])
                arrow = "NARROWS" if d < 0 else "widens "
                if d < 0: narrow += 1
                else: widen += 1
                print(f"    {arrow} {org:13} {prev['created']} {prev['lic']:<16}"
                      f" -> {r['created']} {r['lic']:<16} ({r['id'][:40]})")
            prev = r
    print(f"\n  narrowing transitions: {narrow}")
    print(f"  widening transitions:  {widen}")
    print(f"\n  If these are comparable, 'licences narrow' is not supported and")
    print(f"  the honest claim is only that they CHANGE, unannounced.")
