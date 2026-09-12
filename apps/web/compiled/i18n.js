const cache = new Map();
export async function loadCatalog(locale) {
    const cached = cache.get(locale);
    if (cached)
        return cached;
    const response = await fetch(`./locales/${locale}.json`);
    if (!response.ok)
        throw new Error(`Unable to load locale ${locale}`);
    const catalog = (await response.json());
    cache.set(locale, catalog);
    return catalog;
}
export function translate(catalog, key) {
    return catalog[key] ?? key;
}
