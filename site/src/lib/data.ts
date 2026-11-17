// Loads the published metric tables at build time.
// Every number on the site comes from these CSVs, which pipeline/s06_metrics.py
// writes from the harvested OpenAlex data. Nothing here computes new metrics:
// it only selects, sorts and formats what the pipeline produced.
import fs from 'node:fs';
import path from 'node:path';
import { csvParse, autoType } from 'd3-dsv';

export const DERIVED = path.resolve(process.cwd(), '..', 'data', 'derived');
const METRICS = path.join(DERIVED, 'metrics');

function load<T = Record<string, any>>(name: string, dir = METRICS): T[] {
  const text = fs.readFileSync(path.join(dir, `${name}.csv`), 'utf-8');
  return csvParse(text, autoType) as unknown as T[];
}

export const manifest = JSON.parse(fs.readFileSync(path.join(METRICS, 'manifest.json'), 'utf-8')) as {
  snapshot_date: string;
  generated_at: string;
  works_in_scope: number;
  scope: string;
};

export type Row = Record<string, any>;
export const tables = {
  categoryByYear: load('oa_category_by_year'),
  category: load('oa_category_2015_2025'),
  freeByYear: load('free_to_read_by_year'),
  free: load('free_to_read_2015_2025'),
  fields: load('fields_2015_2025'),
  topics: load('topics_2015_2025'),
  publishers: load('publishers_2015_2025'),
  apcByYear: load('apc_estimates_by_year'),
  apc: load('apc_estimates_2015_2025'),
  coverage: load('corresponding_coverage'),
  books: load('books_and_chapters_2015_2025'),
  green: load('green_opportunity_2015_2025'),
};

/** Cross-check and quality tables. Used only on the Methods page, never blended
 *  into the OpenAlex figures above. */
export const checks = {
  summary: load('summary', path.join(DERIVED, 'crosschecks')),
  doajFeeUnconfirmed: load('doaj_fee_unconfirmed', path.join(DERIVED, 'crosschecks')),
  openapc: load('openapc_summary', path.join(DERIVED, 'crosschecks')),
  exclusions: load('exclusions_summary', path.join(DERIVED, 'quality')),
};
export function check(metric: string) {
  return checks.summary.find((r) => r.metric === metric)!;
}
export function exclusions(reason: string, period = 'complete'): number {
  return checks.exclusions.find((r) => r.exclude_reason === reason && r.period === period)?.works ?? 0;
}
export function openapc(comparison: string) {
  return checks.openapc.find((r) => r.comparison === comparison)!;
}

export function greenFor(key: string) {
  const k = key === 'statewide_no_yale' ? 'statewide_without_yale' : key;
  return tables.green.find((r) => r.entity === k)!;
}

/** OA categories in display order, with plain-language names and meanings. */
export const CATEGORIES = [
  { key: 'diamond', label: 'Diamond', short: 'Diamond',
    meaning: 'Free to read in a journal that charges authors nothing (fee confirmed as $0).' },
  { key: 'oa_fee_unconfirmed', label: 'Open journal, fee not confirmed', short: 'Fee not confirmed',
    meaning: 'Free to read in an open access journal, but the data does not confirm whether authors pay a fee.' },
  { key: 'gold', label: 'Gold', short: 'Gold',
    meaning: 'Free to read in a fully open access journal that usually charges authors a fee.' },
  { key: 'hybrid', label: 'Hybrid', short: 'Hybrid',
    meaning: 'Free to read in a subscription journal because the author paid a fee for this article.' },
  { key: 'bronze', label: 'Bronze', short: 'Bronze',
    meaning: 'Free to read on the publisher’s site without an open license. The publisher could take it back.' },
  { key: 'green', label: 'Green', short: 'Green',
    meaning: 'The journal version is paywalled, but a free copy is in a repository (an online archive).' },
  { key: 'closed', label: 'Closed', short: 'Closed',
    meaning: 'Behind a paywall, and no free copy could be found.' },
] as const;
export type CategoryKey = (typeof CATEGORIES)[number]['key'];

/** Short display names (the long OpenAlex-style name is used in tables). */
export function shortName(key: string): string {
  return entityName(key).replace(' (incl. UConn Health)', '');
}

export const STATEWIDE = 'statewide';
export const STATEWIDE_NO_YALE = 'statewide_no_yale';

export function entityName(key: string): string {
  const r = tables.free.find((x) => x.entity === key);
  return r ? r.entity_name : key;
}

export function institutionKeys(): string[] {
  return tables.free.map((r) => r.entity).filter((k) => k !== STATEWIDE && k !== STATEWIDE_NO_YALE);
}

/** Every institution has a profile page. */
export const PROFILE_KEYS = institutionKeys();

/** Institutions in alphabetical order of their short name. */
export function institutionsAlpha(): string[] {
  return [...institutionKeys()].sort((a, b) => shortName(a).localeCompare(shortName(b)));
}

export function freeFor(key: string) {
  return tables.free.find((r) => r.entity === key)!;
}

export function categoryMix(key: string) {
  return CATEGORIES.map((c) => {
    const r = tables.category.find((x) => x.entity === key && x.oa_category === c.key)!;
    return { ...c, works: r.works as number, share: r.share as number };
  });
}

export function freeTrend(key: string) {
  return tables.freeByYear
    .filter((r) => r.entity === key)
    .sort((a, b) => a.publication_year - b.publication_year)
    .map((r) => ({ year: r.publication_year as number, share: r.free_to_read_share as number,
                   works: r.works as number, free: r.free_to_read as number,
                   incomplete: r.period === 'incomplete' }));
}

export function categoryTrend(key: string) {
  const years = [...new Set(tables.categoryByYear.filter((r) => r.entity === key).map((r) => r.publication_year))].sort();
  return years.map((y) => ({
    year: y as number,
    incomplete: tables.categoryByYear.find((r) => r.entity === key && r.publication_year === y)!.period === 'incomplete',
    parts: CATEGORIES.map((c) => {
      const r = tables.categoryByYear.find((x) => x.entity === key && x.publication_year === y && x.oa_category === c.key)!;
      return { key: c.key, works: r.works as number, share: r.share as number };
    }),
  }));
}

export function topBy(table: Row[], key: string, dim: string, rankCol: 'rank_by_output' | 'rank_by_closed', n = 10) {
  return table
    .filter((r) => r.entity === key && r[rankCol] <= n)
    .sort((a, b) => a[rankCol] - b[rankCol])
    .map((r) => ({ name: String(r[dim]), works: r.works as number, closed: r.closed as number,
                   closedShare: r.closed_share as number }));
}

export function apcFor(key: string) {
  const get = (method: string) => tables.apc.find((r) => r.entity === key && r.method === method);
  const cov = tables.coverage.find((r) => r.entity === key && r.period === 'complete');
  return {
    upper: get('upper_bound_all_authors'),
    corresponding: get('corresponding_author'),
    coverage: cov,
  };
}

export function booksFor(key: string) {
  return tables.books.find((r) => r.entity === key);
}

/** Abbreviations for tight spaces such as chart end labels. These are the
 *  forms each institution commonly uses for itself. */
const ABBREVIATIONS: Record<string, string> = {
  yale: 'Yale', uconn: 'UConn', wesleyan: 'Wesleyan', trinity: 'Trinity', conncoll: 'Conn College',
  quinnipiac: 'Quinnipiac', fairfield: 'Fairfield', sacredheart: 'Sacred Heart', hartford: 'UHart',
  newhaven: 'UNH', scsu: 'SCSU', ccsu: 'CCSU', wcsu: 'WCSU', ecsu: 'ECSU', uscga: 'USCGA',
  bridgeport: 'UB', usj: 'USJ', statewide: 'All 17', statewide_no_yale: 'Without Yale',
};
export function abbreviation(key: string): string {
  return ABBREVIATIONS[key] ?? shortName(key);
}
