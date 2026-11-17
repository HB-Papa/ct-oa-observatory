// Public changelog. Newest first. Add an entry whenever figures, definitions or
// pages change, saying what changed and how much the headline numbers moved.
export const CHANGELOG: { date: string; title: string; items: string[] }[] = [
  {
    date: '2026-11-16',
    title: 'Full site',
    items: [
      'Profiles for all 17 institutions, a Compare page, a Methods and Limitations page, and Downloads with a data dictionary.',
      'New figure: articles that could likely be made free in a repository (a proxy based on what other authors in the same journal have done), with an article list for librarians.',
      'Checks against Unpaywall, OpenAIRE, DOAJ and OpenAPC, summarized on the Methods page. They do not change any figure.',
    ],
  },
  {
    date: '2026-11-16',
    title: 'Meeting abstracts removed',
    items: [
      'Conference abstracts printed in journal supplements (mostly Neurology, The FASEB Journal, Journal of Clinical Oncology, Blood and American Heart Association journals) are no longer counted as articles. 1,279 works from 2015 to 2025 were removed.',
      'Statewide share free to read, 2015 to 2025: 66.8% before, 67.3% after. Without Yale: 59.2% before, 59.6% after.',
    ],
  },
  {
    date: '2026-11-16',
    title: 'First version',
    items: ['Overview of all 17 institutions and a profile of the University of Connecticut, from the OpenAlex snapshot of 2026-11-15.'],
  },
];
