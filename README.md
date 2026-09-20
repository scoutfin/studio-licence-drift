# licence-drift

Do open-model licences narrow over time?

I claimed they did, [in public](https://scoutfin.net/posts/2026-09-20-four-apache-releases/),
on the strength of one model family. This is the check. It refutes me:
**6 narrowing transitions, 11 widening**, across 1,744 models from 16 orgs.

The refutation is the least interesting thing here. The survey got three wrong
answers first, and each one is a distinct failure mode:

1. **`survey.py` — naive adjacency (73/71).** Counted every tier change
   between date-ordered models in an org. 524 of 1,200 adjacent pairs shared
   a creation *date*: different models shipped together, licence tracking
   parameter count. That's catalogue heterogeneity, not drift. The suspiciously
   symmetric result was the tell.

2. **Popularity sampling (2/3).** `sort=downloads&limit=100` gave a download
   floor of 447,472. The model that prompted the whole investigation had 183,
   so the survey structurally could not contain its own subject. **Downloads
   accumulate with age; a licence is fixed at release, when downloads are
   zero.** A popularity-sorted sample of licences only holds licences that
   adoption already ratified. Unioning a `createdAt`-sorted request added 529
   models (30%).

3. **`families.py` — family grouping.** Even then it didn't count, because the
   stem function split `Qwen-Image-2.1` from `Qwen-Image-2512`. Treating a
   trailing version token as a version is a judgement that moves the answer
   from 2/4 to 6/11, so it's documented rather than buried.

Same data, three answers: 73/71, 2/3, 6/11. The tier ranking, the family stem
and the sample sort are all mine. Treat the number accordingly.

## Run

    python3 survey.py      # writes survey.json + survey_union.json
    python3 families.py    # the transition list and the count

Two HTTP requests per org, spaced. Licences read from the `license:` tag in
HF's bulk listing rather than one request per model.

Write-up: https://scoutfin.net/posts/2026-09-20-the-popular-ones-already-got-away-with-it/
