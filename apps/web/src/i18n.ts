import type { Locale, TranslationCatalog } from "./contracts.js";

const cache = new Map<Locale, TranslationCatalog>();

export async function loadCatalog(locale: Locale): Promise<TranslationCatalog> {
  const cached = cache.get(locale);
  if (cached) return cached;
  const response = await fetch(`./locales/${locale}.json`);
  if (!response.ok) throw new Error(`Unable to load locale ${locale}`);
  const catalog = (await response.json()) as TranslationCatalog;
  cache.set(locale, catalog);
  return catalog;
}

export function translate(catalog: TranslationCatalog, key: string): string {
  return catalog[key] ?? key;
}
