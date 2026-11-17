// Data dictionary for the Downloads page and data-dictionary.csv. Reads each
// published CSV's header and pairs every column with its definition from
// downloads.json. The build fails if a column has no definition, so the
// dictionary cannot fall behind the files.
import fs from 'node:fs';
import path from 'node:path';
import catalogue from './downloads.json';
import { DERIVED } from './data';

export interface Column { name: string; meaning: string }
export interface FileEntry {
  path: string; title: string; description: string; license: string; bytes: number; columns: Column[];
}
export interface Group { title: string; id: string; intro: string; license: string; files: FileEntry[] }

const common = catalogue.common_columns as Record<string, string>;
const slug = (s: string) => s.toLowerCase().replace(/[^a-z0-9]+/g, '-').replace(/(^-|-$)/g, '');

function header(file: string): string[] {
  if (!file.endsWith('.csv')) return [];
  const first = fs.readFileSync(file, 'utf-8').split(/\r?\n/, 1)[0];
  return first.split(',').map((c) => c.trim().replace(/^"|"$/g, ''));
}

export const groups: Group[] = catalogue.groups.map((g) => ({
  title: g.title, id: slug(g.title), intro: g.intro, license: g.license,
  files: g.files.map((f: any) => {
    const full = path.join(DERIVED, f.path);
    const own = (f.columns ?? {}) as Record<string, string>;
    const columns = header(full).map((name) => {
      const meaning = own[name] ?? common[name];
      if (!meaning) throw new Error(`downloads.json: no definition for column "${name}" in ${f.path}`);
      return { name, meaning };
    });
    return { path: f.path, title: f.title, description: f.description, license: f.license ?? g.license,
             bytes: fs.statSync(full).size, columns };
  }),
}));

export function size(bytes: number): string {
  if (bytes >= 1e6) return `${(bytes / 1e6).toFixed(1)} MB`;
  if (bytes >= 1e3) return `${Math.round(bytes / 1e3)} KB`;
  return `${bytes} bytes`;
}
