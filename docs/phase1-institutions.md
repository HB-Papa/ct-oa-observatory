# Phase 1: Connecticut institutions in OpenAlex

Snapshot 2026-11-15. Source: `pipeline/s01_institutions_list.py` and `pipeline/s02_institution_counts.py`. Every count is an OpenAlex `group_by` query recorded in `data/logs/query_log.csv`. Phase 1 used 69 credits ($0.0069), keyless.

**Counting rule used here:** articles and reviews, not retracted, where any author lists the institution or one of its sub-units (lineage). 2026 is incomplete. Books and chapters are a separate count. These counts have not yet been spot-checked against the OpenAlex web interface; that happens in phase 2 (`docs/verification.md`).

| OpenAlex ID | Name | Lineage | Role | Articles + reviews 2015–2025 | 2026 (incomplete) | Books + chapters 2015–2025 | All types 2015–2025 |
|---|---|---|---|---:|---:|---:|---:|
| I32971472 | Yale University | I32971472 | named | 117,816 | 12,023 | 7,703 | 170,707 |
| I140172145 | University of Connecticut | I140172145 | named | 40,548 | 3,768 | 3,217 | 70,963 |
| I75929689 | UConn Health | I75929689 | named | 13,196 | 1,493 | 733 | 16,961 |
| I100538780 | Wesleyan University | I100538780 | named | 2,760 | 282 | 435 | 4,166 |
| I56722557 | Trinity College | I56722557 | named | 866 | 50 | 155 | 1,315 |
| I4498119 | Connecticut College | I4498119 | named | 731 | 291 | 148 | 1,152 |
| I43267033 | Quinnipiac University | I43267033 | named | 2,507 | 283 | 306 | 3,489 |
| I126350171 | Fairfield University | I126350171 | named | 1,790 | 182 | 247 | 2,541 |
| I130186095 | Sacred Heart University | I130186095 | named | 1,353 | 152 | 121 | 1,864 |
| I162281398 | University of Hartford | I162281398 | named | 1,217 | 109 | 285 | 2,093 |
| I40253897 | University of New Haven | I40253897 | named | 1,912 | 333 | 190 | 2,729 |
| I35462925 | Southern Connecticut State University | I35462925 › I4210132746 | named | 1,668 | 134 | 242 | 2,323 |
| I154264771 | Central Connecticut State University | I154264771 › I4210132746 | named | 1,408 | 139 | 362 | 2,396 |
| I204366597 | Western Connecticut State University | I204366597 › I4210132746 | named | 424 | 37 | 145 | 656 |
| I203331390 | Eastern Connecticut State University | I203331390 › I4210132746 | named | 577 | 49 | 95 | 950 |
| I186274478 | United States Coast Guard Academy | I186274478 | named | 200 | 18 | 27 | 421 |
| I154300980 | University of Bridgeport | I154300980 | suggested | 763 | 72 | 54 | 1,366 |
| I192633058 | University of Saint Joseph | I192633058 | suggested | 545 | 42 | 91 | 745 |
| I4210110439 | Hartford Seminary | I4210110439 | suggested | 45 | 0 | 7 | 92 |
| I866291873 | Manchester Community College - Connecticut | I4210132746 › I866291873 | suggested | 24 | 3 | 56 | 97 |
| I2800784730 | Post University | I2800784730 | suggested | 17 | 9 | 7 | 44 |
| I176953057 | Albertus Magnus College | I176953057 | suggested | 26 | 1 | 2 | 34 |
| I178721510 | Mitchell College | I178721510 | suggested | 14 | 4 | 0 | 16 |
| I4210164830 | Three Rivers Community College | I4210132746 › I4210164830 | suggested | 3 | 0 | 12 | 34 |
| I205487164 | Norwalk Community College | I205487164 › I4210132746 | suggested | 28 | 2 | 1 | 33 |
| I2803007087 | Holy Apostles College and Seminary | I2803007087 | suggested | 33 | 4 | 5 | 55 |
| I200120152 | Gateway Community College | I200120152 | suggested | 24 | 1 | 0 | 27 |
| I2799467792 | Capital Community College | I2799467792 › I4210132746 | suggested | 12 | 1 | 7 | 22 |
| I71561298 | Goodwin College | I71561298 | suggested | 17 | 0 | 0 | 26 |
| I140172145 + I75929689 | UConn + UConn Health (deduplicated) | — | rollup | 45,991 | 4,249 | 3,526 | 78,459 |
| 29 IDs | Statewide, named + suggested (deduplicated) | — | statewide | 177,841 | 17,955 | 13,976 | 271,039 |
| 28 IDs | Statewide without Yale (deduplicated) | — | statewide | 63,387 | 6,304 | 6,386 | 105,172 |
| 16 IDs | Statewide, named only (deduplicated) | — | statewide | 176,565 | 17,830 | 13,751 | 268,786 |

Lineage `I4210132746` is the Connecticut State Colleges and Universities system, the parent of the four state universities and several community colleges.
