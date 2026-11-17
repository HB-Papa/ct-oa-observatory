// A plain sitemap for search engines, listing every page.
import { PROFILE_KEYS } from '../lib/data';
import { SITE_URL } from '../lib/site';

export function GET() {
  const paths = ['/', '/institutions/', ...PROFILE_KEYS.map((k) => `/institutions/${k}/`),
    '/compare/', '/methods/', '/downloads/', '/about/', '/changelog/'];
  const body = `<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n`
    + paths.map((p) => `  <url><loc>${SITE_URL}${p}</loc></url>`).join('\n') + '\n</urlset>\n';
  return new Response(body, { headers: { 'Content-Type': 'application/xml' } });
}
