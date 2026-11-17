// Public changelog, newest first, stored in changelog.json so the monthly
// refresh (pipeline/refresh_report.py) can add an entry. Add an entry whenever
// figures, definitions or pages change, saying how the headline numbers moved.
import entries from './changelog.json';
export const CHANGELOG: { date: string; title: string; items: string[] }[] = entries;
