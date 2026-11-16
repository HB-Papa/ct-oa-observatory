// Static site: every page is built to plain HTML at build time from the
// pipeline's metric CSVs (../data/derived/metrics). No server, no client
// framework, no analytics.
import { defineConfig } from 'astro/config';

export default defineConfig({
  output: 'static',
  trailingSlash: 'ignore',
  build: { format: 'directory' },
  // No prefetching or other scripts that make background requests.
  prefetch: false,
});
