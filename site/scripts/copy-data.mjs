// Copies the published data files into public/data/ before each build, so the
// Downloads page can link to them. The list of files is src/lib/downloads.json;
// nothing outside that list is copied.
import fs from 'node:fs';
import path from 'node:path';

const site = path.resolve(import.meta.dirname, '..');
const derived = path.resolve(site, '..', 'data', 'derived');
const out = path.join(site, 'public', 'data');
const catalogue = JSON.parse(fs.readFileSync(path.join(site, 'src', 'lib', 'downloads.json'), 'utf-8'));

fs.rmSync(out, { recursive: true, force: true });
let count = 0;
for (const group of catalogue.groups) {
  for (const file of group.files) {
    const from = path.join(derived, file.path);
    if (!fs.existsSync(from)) throw new Error(`Missing data file: ${file.path}`);
    const to = path.join(out, file.path);
    fs.mkdirSync(path.dirname(to), { recursive: true });
    fs.copyFileSync(from, to);
    count += 1;
  }
}
fs.copyFileSync(path.join(derived, 'LICENSE.md'), path.join(out, 'LICENSE.md'));
fs.copyFileSync(path.join(derived, 'crosschecks', 'openapc', 'LICENSE.md'), path.join(out, 'crosschecks', 'openapc', 'LICENSE.md'));
console.log(`copy-data: ${count} files copied to public/data`);
