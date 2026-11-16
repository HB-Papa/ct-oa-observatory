// Number formatting. One place, so every page writes numbers the same way.
const int = new Intl.NumberFormat('en-US');

export const n = (x: number) => int.format(Math.round(x));
export const pct = (x: number, digits = 1) => `${(x * 100).toFixed(digits)}%`;
export const pct0 = (x: number) => `${Math.round(x * 100)}%`;
/** Signed percentage-point change, e.g. "+12.0 percentage points". */
export const points = (x: number) => `${x >= 0 ? '+' : '−'}${Math.abs(x * 100).toFixed(1)} percentage points`;
export const pointsShort = (x: number) => `${x >= 0 ? '+' : '−'}${Math.abs(x * 100).toFixed(1)} pts`;

/** A share in plain words for headlines, e.g. 0.668 -> "two-thirds".
 *  Only used when the share is within 1.5 points of the fraction; otherwise
 *  the exact percentage is returned, so a headline never rounds misleadingly. */
const FRACTIONS: [number, string][] = [
  [1 / 4, 'a quarter'], [1 / 3, 'a third'], [2 / 5, 'two in five'], [1 / 2, 'half'],
  [3 / 5, 'three in five'], [2 / 3, 'two-thirds'], [3 / 4, 'three-quarters'], [4 / 5, 'four in five'],
];
export function inWords(x: number): string {
  const [f, w] = FRACTIONS.reduce((best, cur) => (Math.abs(cur[0] - x) < Math.abs(best[0] - x) ? cur : best));
  return Math.abs(f - x) <= 0.015 ? w : pct(x);
}
export const capitalize = (s: string) => s.charAt(0).toUpperCase() + s.slice(1);

/** Compact dollars: $60.2 million, $1.2 million, $351,536. */
export function dollars(x: number): string {
  if (x >= 1e6) return `$${(x / 1e6).toFixed(1)} million`;
  return `$${int.format(Math.round(x))}`;
}

/** WCAG relative-luminance contrast, used to pick white or near-black text
 *  inside a colored bar segment. */
function lum(hex: string) {
  const c = hex.replace('#', '').match(/.{2}/g)!.map((h) => parseInt(h, 16) / 255)
    .map((v) => (v <= 0.03928 ? v / 12.92 : ((v + 0.055) / 1.055) ** 2.4));
  return 0.2126 * c[0] + 0.7152 * c[1] + 0.0722 * c[2];
}
export function contrast(a: string, b: string) {
  const [x, y] = [lum(a), lum(b)].sort((p, q) => q - p);
  return (x + 0.05) / (y + 0.05);
}
export function inkOn(fill: string) {
  return contrast(fill, '#ffffff') >= contrast(fill, '#141414') ? '#ffffff' : '#141414';
}
