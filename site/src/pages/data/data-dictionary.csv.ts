// The data dictionary as a CSV file, built from the same source as the
// Downloads page: one row per file and column.
import { groups } from '../../lib/dictionary';

const q = (s: string) => (/[",\n]/.test(s) ? `"${s.replace(/"/g, '""')}"` : s);

export function GET() {
  const rows = [['file', 'column', 'meaning', 'license']];
  for (const g of groups) for (const f of g.files) for (const c of f.columns) rows.push([`data/${f.path}`, c.name, c.meaning, f.license]);
  return new Response(rows.map((r) => r.map(q).join(',')).join('\n') + '\n', {
    headers: { 'Content-Type': 'text/csv; charset=utf-8' },
  });
}
