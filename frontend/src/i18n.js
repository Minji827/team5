import { createContext, useContext } from "react";
import { languages, translate, resources } from "./locale";

export const LanguageContext = createContext(null);
export function useI18n() {
  const { locale, setLocale } = useContext(LanguageContext);
  const t = (key, params) => translate(locale, key, params);
  const number = (value) => new Intl.NumberFormat(locale, { maximumFractionDigits: 1, useGrouping: false }).format(value);
  return { locale, setLocale, t, languages,
    minutes: (n) => t("minutes", { n: number(n) }),
    approx: (n) => t("approx", { n: number(n) }),
    walkTime: (n) => t("walkTime", { n: number(n) }),
    stayTime: (n) => t("stayTime", { n: number(n) }),
    placeLabel: (point) => point?.label === "내 위치" ? t("myLocation") : point?.label || t("mapStart"),
    message: (value) => { const text = t(value); return Object.values(resources[locale]).includes(text) ? text : t("requestError"); },
  };
}
