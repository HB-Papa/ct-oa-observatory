// OA category colors. Chosen and checked with the dataviz palette validator
// (2026-11-16), see DECISIONS.md "Chart palette".
// Light, on white #ffffff (re-validated for the report design; green, bronze
// and closed adjusted so labels printed inside bar segments reach 4.5:1):
// every slot clears 3:1 against the page, and neighbouring pairs in stack
// order clear the colorblind (CVD Delta E >= 8) and normal-vision
// (Delta E >= 15) checks. Dark, on #15181d: the same checks pass.
// Closed is a deliberate neutral (not a hue): it is "not open".
export const CATEGORY_COLORS: Record<string, { light: string; dark: string }> = {
  diamond:            { light: '#1c5cab', dark: '#4c7fe6' },
  oa_fee_unconfirmed: { light: '#3a9cc4', dark: '#26a9a0' },
  gold:               { light: '#a87700', dark: '#c98500' },
  hybrid:             { light: '#7a5cd6', dark: '#9085e9' },
  bronze:             { light: '#b84f1b', dark: '#d95926' },
  green:              { light: '#0b7d56', dark: '#199e70' },
  closed:             { light: '#938f86', dark: '#c9c5ba' },
};

// Two-series line charts (an institution vs a comparison), from the reference
// categorical palette slots 1 and 2.
export const SERIES = {
  a: { light: '#2a78d6', dark: '#3987e5' },
  b: { light: '#eb6834', dark: '#d95926' },
};
