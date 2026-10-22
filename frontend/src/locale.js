import resources from "./translations.json" with { type: "json" };

export const languages = { ko: "한국어", en: "English", ja: "日本語", "zh-TW": "繁體中文" };
const sourceKeys = Object.fromEntries(Object.values(resources).flatMap((messages) => Object.entries(messages).map(([key, value]) => [value, key])));
sourceKeys["카페·디저트"] = "cafe";

export function translate(locale, key, params = {}) {
  const id = Object.hasOwn(resources.ko, key) ? key : sourceKeys[key];
  let value = resources[locale]?.[id] ?? resources.ko[id] ?? key;
  if (locale === "en" && id === "placeCount" && params.count === 1) value = "{count} stop";
  for (const [name, replacement] of Object.entries(params)) value = value.replaceAll(`{${name}}`, String(replacement));
  return value;
}
export { resources };
