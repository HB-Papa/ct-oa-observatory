# Cross-checks: how OpenAlex's open access labels compare with other sources

Phase 6. Written by the independent cross-check agent, 2026-11-16. Snapshot of the validation data is 2026-11-15.

OpenAlex stays the only source for numbers on the site. Nothing in this report changes a site figure. The other sources are used only to test OpenAlex, and their numbers are never added to OpenAlex figures.

## Read this first: issues worth acting on

None of these is a coding error in our pipeline's OA classification. Our `oa_category` matches OpenAlex's `oa_status` exactly as designed (all 61 OpenAlex "diamond" works in the sample split into 3 diamond and 58 fee not confirmed, and every other status passes through unchanged). The issues below are either OpenAlex blind spots that hit Connecticut in particular, or places where our own wording promises more than the code does.

1. **OpenAlex misses many free copies in Connecticut's own repositories (an OpenAlex limitation, not our bug).** OpenAlex lists records in bepress Digital Commons repositories (Fairfield, New Haven, Trinity, UConn, Connecticut College and others) and in Yale's EliScholar, but often marks them "not free". I checked three that OpenAlex calls closed. All three repository pages describe an accepted manuscript ("post-print") and show a public Download button. OpenAlex marks each one `submittedVersion`, not free. The PDFs themselves sent our script to a bot check, so I could not open them, but the pages show them as public. Across the dataset, 0 of 560 EliScholar locations are marked free, and only 34% of Fairfield's 216 and 50% of New Haven's 201 are. **553 works that OpenAlex calls closed (2015-2025) have a Digital Commons or EliScholar location marked not free.** That is an upper bound, because some of these records hold only a citation with no file. For scale, that is 0.9% of the 58,479 closed works statewide. Fairfield (88 works) and New Haven (73) are hit hardest relative to their size. Source: `verification/crosscheck_digitalcommons.py`.
2. **Journal of Financial Crises (published by Yale, hosted on EliScholar) is labeled mostly closed or bronze.** In 2015-2025 OpenAlex has 143 closed, 162 bronze, 116 green and 9 hybrid works in this journal, and it marks the journal as not open access. The one closed article I checked resolves to an EliScholar page with a public Download button. The journal looks free to read, so OpenAlex probably understates Yale's free-to-read share by up to about 143 works. Against Yale's 116,949 works that is about 0.1 point.
3. **The green-proxy wording does not match the code (our pipeline, a definition issue).** `s12_green_proxy.py` says a candidate "has no free repository copy yet". The code excludes only free *accepted* or *published* copies. **2,676 of the 8,530 bronze candidates (31%) already have a free copy outside the publisher**, nearly all preprints (submitted versions), and 1,550 of them are on arXiv. Closed candidates are fine: 0 closed works have any free location. Either change the label to "no free accepted or published version in a repository", or drop these works from the candidate list. Chris's call.
4. **Meeting abstracts are counted as articles (a scope question).** OpenAlex types conference abstracts printed in journal supplements as `article`. At least 984 closed works and **at least 1,018 green-proxy candidates** have "supplement" DOIs. These come mainly from Neurology (460 candidates), The FASEB Journal (407), Journal of Clinical Oncology (75), Blood (37) and Circulation (35). Blood has a further 177 closed works whose DOIs follow the meeting-abstract pattern. Nobody deposits a 300-word abstract in a repository, and these abstracts inflate the closed counts slightly. Neurology, the top journal on the candidate list, is mostly abstracts. These counts are lower bounds, because abstracts without "suppl" in the DOI are not caught.
5. **Minor: OpenAlex sometimes files repository copies under a journal with a similar name.** For example, accepted manuscripts in Glasgow's "Enlighten" repository appear under an Indonesian journal called *ENLIGHTEN*, and URI Digital Commons copies appear under *Journal of Media Literacy Education*. Our `has_oa_accepted_repository_copy` flag looks only at locations typed `repository`, so it misses these. The only effect is on green-proxy candidates: 31 bronze works. OpenAlex's own OA status is not affected.

**Follow-up (2026-11-16, after this report):** issues 3, 4 and 5 are fixed in `pipeline/s12_green_proxy.py`. A candidate now has no free copy anywhere except the publisher's own page (this drops free preprints and misfiled repository copies), and meeting abstracts are left out by DOI pattern (1,202 closed or bronze works statewide, a lower bound). Statewide candidates went from 47,456 to 43,581 (24.7% of 2015-2025 articles). The counts quoted in issues 3 to 5 describe the earlier rule. Issues 1 and 2 are OpenAlex limitations and go on the Methods page. Whether to drop meeting abstracts from the main OA figures too is Chris's call (it would move about 1,000 closed works).

## The sample

The sample has 510 Connecticut articles with a DOI, 30 per institution for 17 institutions, published 2015-2025 (`data/derived/crosschecks/sample.csv`). **Because every institution gets the same 30, the overall percentages below are unweighted sample rates. They are not estimates of statewide rates.** Small institutions count as much as Yale.

OpenAlex status in the sample: closed 223, gold 82, diamond 61, bronze 57, green 46, hybrid 41.

## 1. Unpaywall (consistency check only, not independent)

Unpaywall comes from the same nonprofit as OpenAlex (OurResearch), and since late 2025 it runs on the OpenAlex database. Agreement is expected, so this is only a check that the two outputs line up. It does not confirm OpenAlex.

| OpenAlex status | Unpaywall: bronze | closed | gold | green | hybrid | not found |
|---|---:|---:|---:|---:|---:|---:|
| bronze | 57 | 0 | 0 | 0 | 0 | 0 |
| closed | 0 | 223 | 0 | 0 | 0 | 0 |
| diamond | 0 | 0 | 57 | 0 | 0 | 4 |
| gold | 0 | 0 | 82 | 0 | 0 | 0 |
| green | 0 | 0 | 0 | 42 | 0 | 4 |
| hybrid | 0 | 0 | 0 | 0 | 40 | 1 |

Unpaywall found 501 of the 510 DOIs, and **501 of 501 agree** once you allow for Unpaywall having no "diamond" status (it shows diamond as gold). 9 DOIs were not found.

## 2. OpenAIRE (the main independent check)

OpenAIRE is a European research graph built separately from OpenAlex. It found 504 of the 510 DOIs. Its "best access right" was blank for 97 of those. I looked inside the blank records (`verification/crosscheck_inspect.py`). They are mostly records built only from Crossref, or from Crossref plus Microsoft Academic Graph or Europe PMC, with no access information at all. 83 of the 97 are works OpenAlex calls closed. **Blank means "OpenAIRE has no information". It is not counted as closed below.** The figure that would result from counting it as closed is given for comparison.

### 2a. Free to read

| OpenAlex | OpenAIRE OPEN | CLOSED | RESTRICTED | blank | not found |
|---|---:|---:|---:|---:|---:|
| closed (223) | 23 | 116 | 0 | 83 | 1 |
| free to read (287) | 242 | 25 | 1 | 14 | 5 |

- **Where OpenAIRE gives an answer (407 works): 358 agree, 88.0%.** In 23 works OpenAlex says closed and OpenAIRE says open. In 26 works OpenAlex says free and OpenAIRE says closed or restricted.
- If blank were counted as closed, agreement would be 441 of 504, or 87.5%.
- By OpenAlex status, OpenAIRE says OPEN for 82 of 82 gold, 57 of 57 diamond with an answer, 34 of 37 hybrid, 32 of 40 green and 37 of 52 bronze. Bronze is the weakest group, as expected for free-to-read copies with no licence.
- By year of publication: 2015-2019 88.5% (200 compared), 2020-2022 89.0% (127), 2023-2025 85.0% (80).

Per institution (works where OpenAIRE gives an answer, 30 sampled each):

| Institution | Compared | Agree | % agree | OA closed / OAIRE open | OA free / OAIRE not open | Blank or not found | OpenAlex free % | OpenAIRE open % |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| bridgeport | 25 | 25 | 100.0 | 0 | 0 | 5 | 76 | 76 |
| ccsu | 23 | 21 | 91.3 | 2 | 0 | 7 | 43 | 52 |
| conncoll | 23 | 21 | 91.3 | 0 | 2 | 7 | 61 | 52 |
| ecsu | 21 | 19 | 90.5 | 0 | 2 | 9 | 67 | 57 |
| fairfield | 22 | 19 | 86.4 | 3 | 0 | 8 | 64 | 77 |
| hartford | 23 | 19 | 82.6 | 1 | 3 | 7 | 70 | 61 |
| newhaven | 27 | 20 | 74.1 | 3 | 4 | 3 | 67 | 63 |
| quinnipiac | 24 | 23 | 95.8 | 0 | 1 | 6 | 58 | 54 |
| sacredheart | 23 | 20 | 87.0 | 2 | 1 | 7 | 61 | 65 |
| scsu | 27 | 24 | 88.9 | 1 | 2 | 3 | 63 | 59 |
| trinity | 23 | 19 | 82.6 | 4 | 0 | 7 | 52 | 70 |
| uconn | 24 | 20 | 83.3 | 2 | 2 | 6 | 71 | 71 |
| uscga | 22 | 19 | 86.4 | 0 | 3 | 8 | 82 | 68 |
| usj | 22 | 21 | 95.5 | 1 | 0 | 8 | 59 | 64 |
| wcsu | 21 | 19 | 90.5 | 2 | 0 | 9 | 62 | 71 |
| wesleyan | 27 | 25 | 92.6 | 0 | 2 | 3 | 78 | 70 |
| yale | 30 | 24 | 80.0 | 2 | 4 | 0 | 80 | 73 |

With only 21 to 30 works per row, a single disagreement moves a row by 3 to 5 points. Read this table as "no institution stands out as badly classified", not as a ranking.

### 2b. Publisher OA colour

OpenAIRE gives a publisher colour (gold, hybrid, bronze) or none. For comparison, OpenAlex gold and diamond are grouped as gold.

| OpenAlex status | OAIRE none | bronze | gold | hybrid | not found |
|---|---:|---:|---:|---:|---:|
| bronze | 22 | 19 | 8 | 8 | 0 |
| closed | 200 | 13 | 4 | 5 | 1 |
| diamond | 7 | 0 | 51 | 2 | 1 |
| gold | 0 | 0 | 81 | 1 | 0 |
| green | 17 | 21 | 3 | 2 | 3 |
| hybrid | 7 | 0 | 15 | 18 | 1 |

- Agreement overall (504 found, with "none" counting as a match when OpenAlex has no publisher OA): 386, 76.6%.
- When both give a colour: 169 of 203 agree, 83.3%.
- Gold is solid: 81 of 82 gold and 51 of 60 diamond are gold in OpenAIRE.
- Hybrid and bronze are soft in both systems. 15 OpenAlex hybrid works are "gold" in OpenAIRE, and bronze splits all ways. The two systems draw the hybrid/bronze line differently: OpenAlex needs an open licence for hybrid, while OpenAIRE partly infers colour from Crossref licence links.
- 21 OpenAlex green works are "bronze" in OpenAIRE. Many are in journals that make articles free on their own site after a delay (PNAS, Diabetes, Development). OpenAIRE's colour comes from an older Unpaywall feed that saw those publisher PDFs. Today OpenAlex marks the publisher copy not free and counts the work as green through PubMed Central. Either way the article is free to read, so the free-to-read share is unaffected.
- OpenAIRE's "in a diamond journal" flag is almost never set. It is true for 1 of the 61 OpenAlex diamond works, so it cannot be used to test diamond.

### 2c. Repository copy

OpenAlex "has a free repository copy" here means a location with `source_type = 'repository'` and `is_oa` true. OpenAIRE's field is `isGreen`.

| OpenAlex | OAIRE isGreen true | isGreen false | not found |
|---|---:|---:|---:|
| has free repository copy (192) | 114 | 73 | 5 |
| no free repository copy (318) | 4 | 313 | 1 |

- Agreement: 427 of 504, 84.7%. Almost all disagreements go one way: OpenAlex sees a repository copy and OpenAIRE does not.
- Of the 73, 28 have their free copy only in PubMed Central or Europe PMC. OpenAIRE often merges a Europe PMC record without access information, or an older Unpaywall entry marked green, and still sets `isGreen` false.
- Leaving PMC out, OpenAlex has a free non-PMC repository copy for 141 works. OpenAIRE agrees for 96 of them.

## 3. The disagreements, examined by hand

Each disagreement was looked at through the full OpenAIRE record (its "instances", meaning the copies it merged and where each came from), the OpenAlex locations, and the Unpaywall record. All three came from the saved cache (`verification/crosscheck_inspect_out.txt`). I also made a small number of live checks: 25 current OpenAlex work records, 14 landing pages, 5 repository pages, 4 PDF links and 2 journal fee pages, 50 requests in all (`verification/crosscheck_live*.py`). The current OpenAlex records matched our snapshot for every work checked. Many publisher sites (OUP, Wiley, SAGE, PNAS, ASH, ScienceDirect) answered our script with a bot check, so those pages could not be read. Judgments marked "unverified" rest on the evidence in the records only.

### Group A: OpenAlex closed, OpenAIRE open (23 works, all examined)

| Pattern | Works | Who looks right |
|---|---:|---|
| OpenAIRE's "open" comes from an **old Unpaywall entry** that OpenAlex no longer shows as free (a repository PDF, a working paper, or a publisher PDF that was free at some point) | 13 | Mixed. For the 3 Digital Commons accepted manuscripts I checked, **OpenAIRE is right** (the repository offers a public download). One Unpaywall link pointed to an unrelated government PDF (**OpenAlex right**). The publisher PDFs (OUP, Wiley, Lippincott, ASH, FASEB) are unverified. |
| OpenAIRE infers OA from the **Crossref licence link or journal** (OUP's "CHORUS" licence read as hybrid; Wiley/IET terms, Inderscience and Taylor & Francis read as gold) | 9 | OpenAIRE's *colour* is wrong in at least 7 (the CHORUS licence is a public-access promise for US-funded papers, not an open licence or a paid fee). Whether the 5 OUP articles are free to read today is unverified. One case, an Iowa State Digital Press journal, looks like a genuinely open journal that **OpenAlex misses**. |
| OpenAIRE merged a **figshare supplementary file** into the article record | 1 | **OpenAlex right.** The supplement is open, the article is not. |

### Group B: OpenAlex free, OpenAIRE closed or restricted (26 works, all examined)

| Pattern | Works | Who looks right |
|---|---:|---|
| OpenAIRE's record **lacks the repository copy** OpenAlex found (PubMed Central, arXiv, SSRN, PhilPapers, URI Digital Commons, CONICET) | 8 | **OpenAlex right** for the PMC, arXiv, SSRN and PhilPapers copies. The CONICET copy is marked RESTRICTED by the repository itself, so it is unclear. |
| Elsevier **accepted manuscript on ScienceDirect** (`/science/article/am/`), the public-access copy Elsevier hosts for US-funded papers. OpenAIRE reads only the Crossref text-mining licence and says closed | 7 | **OpenAlex probably right.** This is a known Elsevier public-access route. The page answered our script with "open access" text, behind a 403. |
| Elsevier "open access user licence" (open archive or free-to-read) read by OpenAIRE as closed | 4 | **OpenAlex probably right.** That Elsevier licence is a free-to-read licence. |
| Wiley `pdfdirect` or SAGE PDF free on the publisher site (5 bronze, plus 1 hybrid public-domain US government work); OpenAIRE sees only the Crossref licence | 6 | Unverified, because the sites block scripts. OpenAlex's current records still list these links as free. Bronze is the least stable category, so some may have closed since. |
| Journal licence says "pre open access content", OpenAlex says hybrid | 1 | Free to read looks right (the journal is open now). OpenAlex's "hybrid" label looks wrong for a journal that has no fees (Educational Media Reviews Online, Penn State Libraries). |

### Group C: OpenAlex green, OpenAIRE isGreen false (28 works; 20 not already in group B, all 20 examined)

- 15 have their free copy in **PubMed Central or Europe PMC**. OpenAIRE either holds the Europe PMC record with no access value, or holds an Unpaywall instance marked green, and still leaves `isGreen` false. **OpenAlex right.** These PMC links are standard full-text copies.
- 5 are in **SSRN, RePEc/EconStor, CSUSB ScholarWorks, URI Digital Commons or Authorea**. OpenAIRE either did not merge the copy or merged it with no access value. **OpenAlex right** for SSRN and EconStor, and plausible for the rest.
- OpenAIRE's `isGreen` is therefore a narrow flag. It should not be read as "no repository copy exists".

### Group D: OpenAlex free, OpenAIRE blank (14 works; 11 not in the groups above)

All 11 are OpenAIRE records built from Crossref alone. Most are small or new journals: North American Business Press, Al-Kindi, Science Publications and similar. OpenAIRE simply has no access data. Nothing to judge.

### Examples checked

| Group | Work | DOI | OpenAlex | OpenAIRE | Judgment |
|---|---|---|---|---|---|
| A | W2183917196 | 10.1016/j.poly.2015.11.027 | closed; Fairfield Digital Commons copy marked not free, "submittedVersion" | OPEN (old Unpaywall: Fairfield PDF) | OpenAIRE right. Page says author post-print archived with permission and shows Download |
| A | W2442085864 | 10.1080/00036846.2016.1184376 | closed; New Haven Digital Commons copy marked not free | OPEN (old Unpaywall: New Haven PDF) | OpenAIRE right. Page says Accepted Manuscript and shows Download |
| A | W2998909943 | 10.1080/07370016.2020.1693095 | closed; Fairfield Digital Commons copy marked not free | OPEN (old Unpaywall: Fairfield PDF) | OpenAIRE right. Page says Accepted Manuscript and shows Download |
| A | W2808486158 | 10.1007/s11356-018-2493-1 | closed; New Haven Digital Commons copy marked not free | OPEN (old Unpaywall: New Haven PDF) | Probably OpenAIRE right (same pattern, not opened) |
| A | W2279012091 | 10.1080/01603477.2015.1134260 | closed; RePEc copy marked not free | OPEN (working-paper PDF) | Working-paper version on a research-centre site. Unverified, leans OpenAIRE |
| A | W2900793605 | 10.1016/j.exis.2018.10.007 | closed | OPEN bronze (old Unpaywall link to a Ugandan government policy PDF) | OpenAlex right. The link is an unrelated document and now returns an HTML page |
| A | W3095231685 | 10.1182/blood-2020-134718 | closed | OPEN bronze | ASH meeting abstract. To my knowledge these abstracts are free on the ASH site (page blocked our script). Leans OpenAIRE |
| A | W3174498221 | 10.1096/fasebj.2018.32.1_supplement.563.4 | closed | OPEN bronze | FASEB meeting abstract. Unverified |
| A | W2395577023 | 10.2522/ptj.20150453 | closed | OPEN bronze (old Unpaywall: OUP PDF) | Unverified (OUP blocks scripts) |
| A | W2952739627 | 10.1093/geront/gnz083 | closed | OPEN hybrid (Crossref CHORUS licence) | Colour wrong in OpenAIRE. Free-to-read unverified |
| A | W4388484113 | 10.1093/ia/iiad249 | closed | OPEN hybrid (Crossref CHORUS licence) | As above |
| A | W2944866439 | 10.1049/iet-com.2018.5849 | closed | OPEN gold (Crossref Wiley terms licence) | Leans OpenAlex. That licence is a publisher terms page, not an open licence |
| A | W2763826390 | 10.1504/ijmrs.2017.087371 | closed | OPEN gold (Crossref, no licence) | Leans OpenAlex. Inderscience is a subscription publisher |
| A | W2733628627 | 10.31274/jctp-180810-73 | closed; Iowa State repository copy marked not free | OPEN gold (Crossref and Unpaywall) | Leans OpenAIRE. Iowa State Digital Press journal, which looks open access |
| A | W4404196319 | 10.1080/10826084.2024.2422951 | closed | OPEN (figshare supplementary data, CC BY) | OpenAlex right. Only the supplement is open |
| B | W2802843565 | 10.1016/j.jfluidstructs.2018.02.005 | bronze; accepted manuscript on ScienceDirect | CLOSED (Crossref licence only) | OpenAlex probably right (Elsevier public-access accepted manuscript) |
| B | W2616888546 | 10.1016/j.nuclphysa.2017.05.077 | bronze; accepted manuscript on ScienceDirect | CLOSED | As above |
| B | W3016286018 | 10.1016/j.tcs.2020.03.024 | bronze; publisher free | CLOSED (Elsevier open-access user licence) | OpenAlex probably right. That licence means free to read |
| B | W4390579385 | 10.1016/j.cell.2023.12.004 | hybrid CC BY | CLOSED | OpenAlex probably right. OpenAIRE misread the licence |
| B | W2966026939 | 10.1002/da.22944 | hybrid, public domain | CLOSED (Wiley terms licence) | OpenAlex probably right (US government work) |
| B | W4386481910 | 10.1111/geb.13747 | bronze; Wiley pdfdirect (current record still free) | CLOSED | Unverified |
| B | W4283324890 | 10.1111/1365-2664.14242 | bronze; Wiley pdfdirect | CLOSED | Unverified |
| B | W3217125567 | 10.1177/02662426211020608 | bronze; SAGE PDF | CLOSED | Unverified (SAGE blocks scripts) |
| B | W3136610339 | 10.1002/nau.24649 | green; PMC accepted manuscript | CLOSED | OpenAlex right (PMC) |
| B | W4388493819 | 10.1016/j.jor.2023.11.006 | green; PMC | CLOSED | OpenAlex right |
| B | W4403680470 | 10.1016/j.laa.2024.10.022 | green; arXiv | CLOSED | OpenAlex right |
| B | W4417267801 | 10.1103/k29c-d5ry | green; arXiv and Frankfurt repository | CLOSED (Crossref only) | OpenAlex right |
| B | W4200118937 | 10.1108/raf-10-2020-0295 | green; SSRN | CLOSED (Crossref only) | OpenAlex right |
| B | W4296619485 | 10.1007/s11712-022-09854-8 | green; PhilPapers | CLOSED (Crossref only) | OpenAlex right |
| B | W2915221485 | 10.1016/j.bbr.2019.02.035 | green; CONICET copy | RESTRICTED (CONICET's own label) | Unclear |
| B | W7204186396 | 10.59236/emro.v3i7a1315 | hybrid | CLOSED ("pre open access content" licence) | Free looks right. OpenAlex "hybrid" looks wrong for a no-fee journal |
| C | W2576203379 | 10.1073/pnas.1613422114 | green; PMC | OPEN bronze, isGreen false | Both say free. OpenAIRE's bronze is plausible (PNAS opens after 6 months) |
| C | W2529055067 | 10.2337/db16-0414 | green; PMC | OPEN bronze, isGreen false | Same pattern (Diabetes) |
| C | W2291751883 | 10.1242/dev.130849 | green; PMC | OPEN bronze, isGreen false | Same pattern (Development) |
| C | W2550723764 | 10.1016/j.ajog.2016.11.1036 | green; PMC accepted manuscript | OPEN, isGreen false | OpenAlex right. OpenAIRE's green flag is missing |
| C | W3047210216 | 10.1016/j.drugalcdep.2020.108210 | green; PMC accepted manuscript | OPEN, isGreen false | As above |
| C | W2560394122 | 10.1007/s11293-016-9521-7 | green; Trinity RePEc working paper | OPEN, isGreen false | OpenAlex right |
| C | W1498500411 | 10.1007/s10272-015-0542-2 | green; SSRN, EconStor | OPEN gold, isGreen false | OpenAlex right. Intereconomics is free on the publisher site too, so OpenAIRE's gold is plausible |
| C | W2883130665 | 10.1016/j.erss.2018.06.018 | green; URI Digital Commons | OPEN, isGreen false | OpenAlex right |
| C | W4280500738 | 10.1142/s2010139222500045 | green; SSRN | blank | OpenAlex right |

**Summary of the pattern.** The two systems agree on free-to-read for 88% of the works where OpenAIRE has an answer. Most disagreements come from what each system was fed, not from errors in OpenAlex's rules:

- OpenAIRE still carries old Unpaywall data, so it remembers copies that OpenAlex has since stopped counting.
- OpenAIRE reads Crossref licence links that do not mean open access.
- OpenAIRE fails to merge repository copies that OpenAlex has.

One real OpenAlex weakness shows through: repository copies in bepress Digital Commons and EliScholar are often recorded as not free when they are. This matters more for Connecticut than for most places, because many Connecticut institutions use Digital Commons.

## 4. DOAJ

Source: `verification/crosscheck_doaj.py`, `data/derived/crosschecks/doaj_*.csv`.

**(i) What DOAJ says about the 8,349 "fee not confirmed" works (2015-2025):**

| DOAJ answer for the journal | Works | % |
|---|---:|---:|
| Not in DOAJ | 4,599 | 55.1 |
| In DOAJ, no fee | 2,706 | 32.4 |
| In DOAJ, charges a fee | 858 | 10.3 |
| Published before the journal's DOAJ open access start year | 103 | 1.2 |
| In DOAJ, no APC but other charges | 83 | 1.0 |

- The largest not-in-DOAJ journals are Cureus (549), Oncotarget (149), Journal of Athletic Training (110), Archives of Pathology & Laboratory Medicine (85) and Journal of Clinical and Translational Hepatology (70). Most of these are free to read but are not vetted open access journals, and some charge fees (Oncotarget does: one Connecticut Oncotarget article appears in OpenAPC with a €3,131 payment).
- The largest fee-charging journals are Kidney360 (107 works, $1,800), Chemical Science (65, £2,850), ACG Case Reports Journal (51, $500) and Journal of Thoracic Disease (47, $1,900). Some of these charge only since a recent change of model, and DOAJ shows only today's policy.
- In plain terms: DOAJ could move about a third of "fee not confirmed" works (2,706) into "diamond", but only if we accept that today's no-fee policy also applied in the year of publication. More than half cannot be resolved with DOAJ. Keeping the "fee not confirmed" category is justified.

**(ii) "Diamond" works (fee confirmed $0) whose journal DOAJ now lists with a fee.** Of 1,609 diamond works, 1,414 are in journals DOAJ lists as no-fee and 69 are in journals not in DOAJ. 126 are in journals DOAJ lists with a fee, or **121** counting only works published in or after the journal's DOAJ open access start year (this matches the 121 in the brief). They are spread over 28 journals. The largest are Quantitative Economics (19), Theoretical Economics (19), Precision Radiation Oncology (13) and International Journal of Nursing Sciences (11).

- **Quantitative Economics and Theoretical Economics (Econometric Society).** I read the fee pages DOAJ links to. Both require society membership and charge a submission fee of US$100 (US$50 for students). Both say a publication fee "at 100% of the cost of production per page ($24 per page at the present time)" applies to papers *submitted on or after January 1, 2026*. DOAJ's $1,000 and $840 are therefore page charges that start in 2026. They are not a standard APC, and they did not apply on these terms to the 2015-2025 works. The pages do not say whether a smaller page fee applied before 2026. OpenAlex's $0 is defensible for these years, but "no author charges" is not strictly true: there were submission fees and a membership requirement.
- Most of the rest are journals launched or sponsored under publishers that waive the fee for a period (KeAi and Elsevier titles such as International Journal of Nursing Sciences, Liver Research and Global Health Journal; new Wiley and Springer titles such as mLife, Brain-X and Discover Public Health). Fees were probably added later. This is my general knowledge, not something checked journal by journal.
- Quantitative Biology has 7 diamond works from 2017 onward, but DOAJ's open access start is 2022, so the earlier works predate its open access period.
- For the site: 121 works is 7.5% of diamond. That is worth one sentence on Methods ("a journal's fee status can change; a small number of diamond works are in journals that charge fees today"). It does not justify changing the category.

**(iii) OpenAlex `is_in_doaj` vs our DOAJ lookup, 3,330 journals checked:** both say listed for 1,615, both say not listed for 1,710, and OpenAlex says listed but our ISSN lookup found nothing for 5. **Agreement is 99.8%.** The 5 are probably ISSN mismatches or journals removed from DOAJ: European Review of Latin American and Caribbean Studies, Frontiers of Agricultural Science and Engineering, The Southwest Respiratory and Critical Care Chronicles, Business Ethics and Leadership, Journal of Advanced Computing Systems.

**(iv) Top journals, APC list price (OpenAlex `apc_usd` vs DOAJ maximum in USD).** Of 84 top journals, 45 are in DOAJ and 34 have a USD price in both: 10 are equal, 18 are higher in DOAJ and 6 are lower, with a median difference of +3.4%. Examples:

| Journal | CT articles | OpenAlex $ | DOAJ $ | Difference |
|---|---:|---:|---:|---:|
| PLoS ONE | 1,468 | 2,382 | 2,477 | +4.0% |
| Nature Communications | 1,405 | 6,990 | 7,350 | +5.2% |
| Scientific Reports | 1,234 | 2,690 | 2,850 | +5.9% |
| The Astrophysical Journal | 1,087 | 4,499 | 3,162 | -29.7% |
| eLife | 392 | 2,500 | 3,750 | +50.0% |
| Science Advances | 365 | 4,500 | 5,450 | +21.1% |
| Journal of the American Heart Association | 305 | 3,810 | 3,180 | -16.5% |
| The Astrophysical Journal Letters | 279 | 2,400 | 2,978 | +24.1% |

The usual gap is small and in the direction expected from price rises: OpenAlex's price is older and DOAJ's is current. The large gaps are journals with unusual pricing. The AAS journals (ApJ, AJ, ApJL) charge by article length, so any single "maximum" is arbitrary. eLife changed its publishing model in 2023. Several big journals report prices only in GBP, EUR or CHF in DOAJ (BMJ Open, MNRAS, Frontiers), so no USD comparison is possible. On Methods, this supports the existing wording that APC estimates use list prices from one point in time, which may differ from current prices by several percent and, for a few journals, by 20-50%.

The top journals that both OpenAlex and DOAJ say are *not* in DOAJ, although OpenAlex marks them open access, are Cureus and several large MDPI titles (IJMS, IJERPH, Nutrients, J Clin Med, Cancers) plus Oncotarget. I did not check why. The two sources agree, so it does not affect the comparison.

## 5. OpenAPC

Source: `data/derived/crosschecks/openapc_summary.csv`, `verification/crosscheck_openapc.py`.

**What the summary says, in plain terms.** No Connecticut institution reports to OpenAPC. But 858 Connecticut articles had their fee paid by a co-author's institution or funder that does report, mostly in Europe and including the Gates Foundation. Where a euro list price exists in OpenAlex:

- **Gold articles (255): the fee actually paid was 77% of today's list price in total** (median article 76%). For articles published 2015-2019 it was 68%, and for 2020-2025 it was 87%. Prices have risen, so today's list price overstates older years most.
- **Hybrid articles (138): paid was 71% of list price** (67% for 2015-2019, 78% for 2020-2025).
- Comparing whole journals rather than the same articles gives the same picture: 73% for gold (covering 37% of Connecticut gold works) and 75% for hybrid (32%).
- So a list-price APC estimate is an upper bound, probably by roughly a quarter. It is not a measure of what Connecticut paid.

**Spot check of 10 random matched rows (seed fixed in the script).** All 10 look right. Every row's DOI matches the OpenAlex DOI exactly (858 of 858) and the publication year matches. The OpenAPC payment year is within one year of publication for 852 of 858. Euro values run from €88 to €10,899, with a median of €2,298 and no zero or negative values. Sample rows: Scientific Reports €1,590 (list €2,390); Nature Communications €6,264 (list €5,890, plausible with VAT); Biological Psychiatry hybrid €3,517 (list €5,130); Journal of Neuroscience hybrid €1,611; Frontiers in Nutrition €3,017. One low value stands out: Global Change Biology hybrid at €299 against a €3,870 list price, reported by Stockholm University. It is probably a transformative-agreement share or a partial payment, not an error in our match. Every work matches at most one OpenAPC row.

**The library-funded SCOAP3 case.** 47 Connecticut works that we call diamond appear in OpenAPC with payments totalling €12,192, at a median of €169. All 47 are in the particle-physics journals Journal of High Energy Physics, European Physical Journal C and Physics Letters B. These journals charge authors nothing because SCOAP3, a library consortium, pays the publisher. A member library (mostly RWTH Aachen) reports its per-article share to OpenAPC. That is a library subscription cost, not an author fee, so the diamond label is fair. Two rows report full-size fees (€3,437 from Glasgow for a JHEP article, €1,170 from TU München for a Physics Letters B article). I could not tell why. The other 8 no-fee works with an OpenAPC payment are all "fee not confirmed" (€12,348 in total, median €1,458: Oncotarget, BMJ Public Health, Obstetrics and Gynecology Research and others). Those are real author fees, which supports keeping these works out of "diamond".

Also worth knowing: 11 matched works carry an OpenAPC *hybrid* fee but are bronze (4), green (5) or closed (2) in OpenAlex. A paid hybrid fee normally comes with an open licence, so OpenAlex probably missed the licence on these few. It is too small to matter for the site.

## 6. Green OA proxy

Source: `verification/crosscheck_green_proxy.py`, `verification/crosscheck_journal_probe.py`.

**The rule.** A journal "shows deposit evidence" when at least 3 of its articles worldwide in 2015-2025 are free only through an accepted manuscript in a repository other than PubMed Central or Europe PMC.

**Does the candidate list exclude works that are already free in a repository?**
- Closed candidates: yes. No in-scope closed work has any free location (0).
- Bronze candidates: only partly. See issue 3 at the top. 2,676 of 8,530 bronze candidates already have a free non-publisher copy, nearly all preprints (arXiv 1,550, OSTI 402, HAL 210). A further 31 bronze works have a free accepted or published copy that OpenAlex files under a wrongly matched journal (issue 5).

**Plausibility of flagged journals.** This is my general knowledge of publisher self-archiving policies, not a lookup in a policy database such as Open Policy Finder.

| Journal (flagged) | Publisher | Evidence articles | CT candidates | Plausible? |
|---|---|---:|---:|---|
| Neurology | Wolters Kluwer (AAN) | 31 | 782 | Plausible for articles, but most CT candidates (460) are meeting abstracts |
| J. Am. Acad. Dermatology | Elsevier | 6 | 752 | Yes. Elsevier allows accepted-manuscript deposit after an embargo |
| Biological Psychiatry | Elsevier | 11 | 544 | Yes |
| The Astrophysical Journal | IOP / AAS | 17 | 527 | Yes. AAS allows posting; much of the field uses arXiv |
| The FASEB Journal | Wiley | 17 | 516 | Plausible for articles (Wiley allows deposit after an embargo), but 407 CT candidates are abstracts |
| Int. J. Radiation Oncology Biology Physics | Elsevier | 14 | 490 | Yes |
| J. Am. Acad. Child & Adolescent Psychiatry | Elsevier | 10 | 395 | Yes |
| Blood | ASH (Elsevier since 2024) | 24 | 338 | Plausible for articles. Many CT items are ASH abstracts |
| American Journal of Obstetrics and Gynecology | Elsevier | 10 | 288 | Yes |
| Drug and Alcohol Dependence | Elsevier | 23 | 231 | Yes |
| Environmental Science & Technology | ACS | 80 | 199 | Yes. ACS allows accepted-manuscript posting after 12 months |
| PEDIATRICS | AAP | 17 | 204 | Uncertain. I do not know AAP's current policy well |

**Plausibility of not-flagged journals.**

| Journal (not flagged) | Publisher | Evidence articles | CT closed/bronze | Comment |
|---|---|---:|---:|---|
| Journal of the American College of Cardiology | Elsevier | 1 | 616 | Probably a false negative. Elsevier policy usually allows deposit after an embargo |
| Cell | Elsevier (Cell Press) | 0 | 198 | Probably a false negative (Cell Press allows the accepted manuscript after 12 months) |
| Journal of General Internal Medicine | Springer Nature | 0 | 270 | Probably a false negative. Springer allows accepted-manuscript deposit after 12 months; deposits here go to PMC, which the rule excludes |
| Proceedings of the National Academy of Sciences | NAS | 0 | 233 | Not flagging it is reasonable for a different reason. PNAS makes articles free after 6 months, so deposit adds little |
| Journal of Financial Crises | Yale | 0 | 305 | Correctly not a deposit target. The journal appears to be free already (issue 2) |

**Overall.** The proxy is **conservative for big medical journals**. Their accepted manuscripts mostly sit in PubMed Central (excluded by design) or become free on the publisher site, so worldwide "non-PMC accepted manuscript" evidence is thin even where policy allows deposit. It is also **inflated by meeting abstracts**. The share of journals flagged varies by publisher in a believable way (IEEE 88%, Elsevier 70%, University of Oxford 60%, Wiley 55%, Springer Nature 49%, Wolters Kluwer 45%, SAGE 43%, Informa 41%, De Gruyter 25%). The label "proxy" is essential, and so is the advice to check Open Policy Finder before acting on any single article.

## 7. CORE

Not run. Chris has emailed CORE to confirm its licence terms, and this check is pending until CORE replies. CORE would be the most useful next check for issue 1, because it harvests full text from Digital Commons repositories directly.

## 8. What this means for the site

**State as limitations on the Methods page:**
1. *Independent agreement.* "On a test sample of 510 Connecticut articles, the independent OpenAIRE Graph agreed with OpenAlex on whether an article is free to read for 88% of the articles where it had an answer. Unpaywall, made by the same organisation as OpenAlex, agreed on all 501 it found. The sample has equal numbers per institution, so these are sample rates."
2. *Repository copies in Connecticut's own repositories are undercounted.* OpenAlex often does not recognise free files in bepress Digital Commons and EliScholar. Some articles shown as closed are in fact free in their institution's repository. This affects Fairfield, New Haven and Yale (EliScholar) most visibly. It would not change any headline share by more than about a point, but librarians at those institutions will notice it.
3. *Bronze is the least stable category.* Bronze means free on the publisher site with no open licence. Publishers can withdraw it, and the two systems disagree on it most. The site already ties the 2023-2025 dip to bronze, and this check supports treating bronze changes cautiously.
4. *Hybrid vs bronze vs gold depend on licence data.* The two systems draw these lines differently: both agree on the publisher colour only 83% of the time when both give one, and hybrid is the softest. The free-to-read total is more reliable than the split between colours.
5. *Fee status can change.* A small number of "diamond" works (121) are in journals that charge fees today. "Fee not confirmed" cannot be resolved with DOAJ for more than half its works.
6. *APC estimates are list-price upper bounds.* Actual payments in OpenAPC were about 71-77% of today's list price, and lower for older articles.
7. *Meeting abstracts* in journal supplements are counted as articles, unless Chris decides to exclude them (issue 4).

**Anything that suggests an error in our pipeline?** No error in the OA classification itself: Unpaywall matches OpenAlex 501 for 501, and our diamond split behaves exactly as specified. The pipeline items to decide on are the green-proxy candidate definition (issue 3) and whether to drop meeting abstracts (issue 4). Neither changes any free-to-read figure. The Digital Commons and EliScholar undercount (issues 1 and 2) is an OpenAlex data problem. Under our rules we report OpenAlex as it is and disclose the problem; we do not patch it with other sources. It could be reported to OpenAlex.

## Scripts and outputs (all in `verification/`)

| Script | What it does | Output |
|---|---|---|
| `crosscheck_compare.py` | Agreement tables (Unpaywall, OpenAIRE a/b/c, per institution, by year) | `crosscheck_compare_out.txt`, `crosscheck_disagreements.csv` |
| `crosscheck_inspect.py` | Side-by-side OpenAlex / OpenAIRE / Unpaywall evidence for each disagreement, from the cache | `crosscheck_inspect_out.txt` |
| `crosscheck_live.py`, `crosscheck_live_pdfs.py`, `crosscheck_live_dcpages.py`, `crosscheck_live_fees.py` | 50 live requests: current OpenAlex records, landing pages, repository pages, fee pages | `crosscheck_live_out.json`, `crosscheck_live_pdfs_out.json`, `crosscheck_live_fees_out.txt` |
| `crosscheck_digitalcommons.py` | Sizes the Digital Commons / EliScholar pattern | `crosscheck_digitalcommons_out.txt` |
| `crosscheck_doaj.py` | DOAJ summaries (i)-(iv) | `crosscheck_doaj_out.txt` |
| `crosscheck_openapc.py` | OpenAPC spot checks and the SCOAP3 split | `crosscheck_openapc_out.txt` |
| `crosscheck_green_proxy.py`, `crosscheck_journal_probe.py` | Green-proxy exclusion checks, flagged and not-flagged journals, meeting abstracts, Journal of Financial Crises | `crosscheck_green_proxy_out.txt`, `crosscheck_journal_probe_out.txt` |

Run each from the project root with `python -m verification.<name>`. The OpenAlex API key is read from `.env` and is never printed or saved. No Unpaywall calls were made, so the contact email was not used.
