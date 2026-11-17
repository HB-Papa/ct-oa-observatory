# Accessibility audit

Date: 2026-11-16
Target: WCAG 2.2 level AA
Site tested: the local dev server (http://localhost:4321), then a production build (`npm run build`, 25 pages, no scripts in the output).

## Tools and versions

- axe-core 4.14.0 (the project's dev dependency), rule sets wcag2a, wcag2aa, wcag21a, wcag21aa, wcag22aa and best-practice. Run inside the browser pane (Chromium) on every page, at 1280px and 320px wide, in light and dark color schemes.
- Lighthouse 12.6.1, accessibility category only, headless Chrome 157 (installed Chrome found at `C:\Program Files\Google\Chrome`). Lighthouse uses its default mobile emulation.
- Manual checks in the browser pane: keyboard only, 320px width, the WCAG 1.4.12 text spacing style, small scripts to measure target sizes, heading order, link text, table markup and page titles.

## Pages tested

All 25 outputs: `/`, `/institutions/`, the 17 profiles (yale, uconn, wesleyan, trinity, conncoll, quinnipiac, fairfield, sacredheart, hartford, newhaven, scsu, ccsu, wcsu, ecsu, uscga, bridgeport, usj), `/compare/`, `/methods/`, `/downloads/`, `/about/`, `/changelog/` and the 404 page.

## Results

### axe-core

| Run | Pages | Violations before | Violations after |
|---|---|---|---|
| Light, 1280px | 25 | 0 | 0 |
| Dark, 1280px | 25 | 0 | 0 |
| Light, 320px | 25 | 2 (`/` and every profile: `scrollable-region-focusable`, see issue 1) | 0 |
| Dark, 320px | 25 | 2 (same) | 0 |

The 2 counted before are the home page and the profile pages as a group; the same rule failed on all 18 pages that have the line chart.

"Needs review" items (axe could not decide), same in light and dark:

- Home and every profile: 15 to 18 SVG text items in the line chart (axis labels and end labels). axe cannot read a background behind SVG text. Confirmed by hand: axis labels use the muted text color, 7.6:1 on white and 9.4:1 on the dark page; end labels use the main text color (17.7:1 light). Reviewed earlier at 7.6:1; nothing new here.
- Compare: 80 table cells at 1280px (321 at 320px). These are cells inside the sideways-scrolling table regions, partly out of view, so axe cannot see their background. They use the normal body text color on the page background (about 14:1 in both schemes). Pass.
- Segmented bar labels (the percentages printed inside colored bars) were measured directly: lowest contrast 4.65:1 light (gold) and 4.74:1 dark (bronze), all at or above 4.5:1.

### Lighthouse (accessibility score)

| Page | Score | Failed audits |
|---|---|---|
| `/` | 100 | none |
| `/institutions/uconn/` | 100 | none |
| `/compare/` | 100 | none |
| `/methods/` | 100 | none |
| `/downloads/` | 100 | none |

Each run lists 10 items Lighthouse says to check by hand; the keyboard and focus checks below cover them.

### Keyboard (/, the UConn profile, /compare/, /downloads/)

- The first Tab shows the "Skip to main content" link. Enter moves focus to `<main>` and the next Tab goes to the first link in the content. Pass.
- Tab order follows the reading order on all four pages: skip link, site name, navigation, content, footer. No keyboard traps; Tab moves on past the end of the page and back to the start.
- Every link, summary, checkbox and scroll region shows the 3px blue focus outline (#1d4ed8 light, #93c5fd dark). Pass.
- "Show the numbers as a table": Enter opens it and Space closes it.
- Table regions (`.table-scroll`) can take focus once their table is open, and the arrow keys scroll them sideways.
- Compare: Space ticks and unticks each checkbox. Ticking UConn and New Haven left only those two rows in every table and figure, and the status line changed to "Showing your choices only". Tab order runs across the two columns row by row, which matches the alphabetical order. Pass.
- Downloads: every file link and every "Columns" summary can be reached. Each summary already has a hidden "in <file title>" so it has a unique name.

### Reflow at 320px (equal to 400% zoom)

All 25 pages at 320px: the page never scrolls sideways (`scrollWidth` equals `clientWidth`). Nothing overflows outside the intended scroll regions (tables and the line chart). No clipped or overlapping text found. The segmented bars hide their inside labels at narrow widths as designed, and the table keeps every value.

### Text spacing (WCAG 1.4.12)

I injected line-height 1.5, paragraph spacing 2em, letter spacing 0.12em and word spacing 0.16em on `/`, `/compare/`, two profiles, `/methods/`, `/downloads/`, `/about/`, `/changelog/` and 404, at 320px and 1280px.
- Before: the home page's "most closed articles" bars pushed their value text past the screen edge, and on Downloads and Methods long unbreakable text (`pipeline/s05_quality_report.py`, a DOI) made the page scroll sideways. See issues 2 and 3.
- After: no sideways scroll and no clipped text on any of them.

### Target size (WCAG 2.5.8, 24 by 24 CSS px)

Measured every link, summary, checkbox and focusable region on 8 page types at 1280px and 320px.
- Navigation links: about 36px tall. Pass.
- "Show the numbers as a table" summaries: about 33px tall. Pass.
- Compare checkboxes: the box is 20 by 20px. Each label is tied to its box, so clicking the label ticks the box too. Rows are 36px apart, which meets the spacing exception (no other target lies within the 24px circle). Pass.
- Institution names in the bar lists and the "Sections" links on Downloads and Methods: 18 to 21px tall. They are spaced about 30px apart, so they pass under the spacing exception.
- Footer links and links in running text: inline in a sentence, so they are exempt. Pass.
- Site name link: 22px tall, but it is wide and no other target is close by. Pass under the spacing exception.

### Other specific checks

- Language: `<html lang="en">` on every page. Pass.
- Page titles: all 25 are unique and describe the page (for example "University of Hartford · Connecticut Open Access Observatory"). Pass.
- Headings: exactly one h1 per page and no skipped levels on any page. Pass.
- Link text: no "click here", "more" or bare "CSV" links. No link text is reused for two different destinations, with one small exception: on Methods, "Downloads page" points to `/downloads/` once and to `/downloads/#data-quality` once. Both go to the same page, so this is acceptable.
- Tables: all 26 on Downloads and all others have a caption (hidden on Downloads, visible elsewhere). Every `th` has a `scope`. Pass.
- "Estimate" and "Proxy" tags: real text in red with a border. They do not depend on color alone. A screen reader reads them as part of the heading ("Fees and repository candidates Estimate Proxy"). That is clear enough and I left it.
- Compare structure: a `fieldset` and `legend` ("Institutions to compare") group the boxes. Every checkbox has a real `<label for>`. Choices are not shown by color alone: the native checkmark shows them. Statewide bars differ by color, but they are also bold and named "All 17" or "Without Yale".
- Charts: every SVG chart is hidden from screen readers, and each figure has a written summary and a table. The legends use text labels, and the line chart has direct end labels and a hollow marker for the incomplete year.

## Issues found and fixed

1. **Line chart could not be scrolled with the keyboard on narrow screens.** WCAG 2.1.1 Keyboard (axe `scrollable-region-focusable`). At 320px the chart is wider than the screen, so it scrolls sideways, but its scroll box could not take focus. Recent Chrome and Firefox work around this, but other browsers do not.
   Fix: `src/components/LineChart.astro`. The scroll box now has `tabindex="0"`, `role="region"` and the label "Line chart, scrolls sideways on narrow screens. The same numbers are in the table below." In `src/styles/global.css`, a focus outline offset to match the table regions. Checked: Tab reaches it, arrow keys scroll it, and the outline shows.
2. **Bar values ran off the screen with wider text spacing.** WCAG 1.4.12 Text Spacing and 1.4.10 Reflow. The value text beside each bar ("15,667 closed of ... (37%)") was set to never wrap.
   Fix: `src/styles/global.css`. Removed `white-space: nowrap` from `.bar-val`. At normal spacing nothing changes: I checked every bar value on 4 pages at 4 widths and none wrap. The text now wraps only when it would otherwise run off the screen.
3. **Long file names and DOIs made the page scroll sideways with wider text spacing.** WCAG 1.4.12 and 1.4.10.
   Fix: `src/styles/global.css`. Added `overflow-wrap: break-word` to `body`. This breaks a word only when it cannot fit on a line. It does not change table column widths.
4. **Improvement: the data table toggles all had the same name.** WCAG 2.4.6 Headings and Labels (best practice, not a failure). A profile page has six "Show the numbers as a table" toggles, and in a screen reader's list of controls they all sounded the same.
   Fix: `src/components/Figure.astro`. Added hidden text so each one is read as "Show the numbers as a table for Figure N". The visible text is unchanged and the accessible name still starts with it (2.5.3 Label in Name).
5. **Improvement: the Compare status line was not announced.** WCAG 4.1.3 Status Messages. When the first box is ticked, the sentence under the boxes changes to "Showing your choices only", but screen readers were not told.
   Fix: `src/pages/compare.astro`. Added `role="status"` to that sentence. Without scripts, how this is announced depends on the browser and screen reader. Chrome usually reads the new sentence; others may not. Nothing is lost if they don't: the sentence is still in the fieldset, right after the boxes.

After the fixes: axe shows 0 violations on all 25 pages in light and dark, at 1280px and 320px (100 runs). `npm run build` finishes (25 pages) and the output has no `<script>` tags.

## Left for Chris

- **Screen reader testing.** No real screen reader (NVDA, JAWS, VoiceOver) was used. Before launch, spend 15 minutes with NVDA on Windows on the home page, one profile and Compare, to check how the "Estimate" and "Proxy" tags in headings sound and whether the Compare status line is announced.
- **Compare does not limit the number of choices.** The page says "two to four", but nothing stops someone ticking more, and a page with no JavaScript cannot enforce a limit. This is not an accessibility failure. Consider changing the wording to "two to four work best".
- **Native checkboxes in dark mode.** The unticked boxes use the browser's built-in dark style with the red accent color. They were clearly visible in testing. Their outline contrast is set by the browser, not by the site, so I did not change it.
- **Chart colors.** None changed. Bar and line colors were not checked again here beyond what axe and the earlier validator cover. The charts are hidden from screen readers and their numbers are always in tables, so no color issue was found.
- **Lighthouse** ran in its default mobile mode only. Desktop mode was not run, but axe covered 1280px.
