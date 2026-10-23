import { createContext, useContext } from "react";
import { languages, translate, resources, formatDuration } from "./locale";

export const LanguageContext = createContext(null);
export function useI18n() {
  const { locale, setLocale } = useContext(LanguageContext);
  const t = (key, params) => translate(locale, key, params);
  const duration = (value) => formatDuration(locale, value);
  return { locale, setLocale, t, languages,
    minutes: (n) => duration(n),
    approx: (n) => t("approx", { time: duration(n) }),
    walkTime: (n) => t("walkTime", { time: duration(n) }),
    stayTime: (n) => t("stayTime", { time: duration(n) }),
    placeLabel: (point) => point?.label === "내 위치" ? t("myLocation") : point?.label || t("mapStart"),
    message: (value) => { const text = t(value); return Object.values(resources[locale]).includes(text) ? text : t("requestError"); },
  };
}
