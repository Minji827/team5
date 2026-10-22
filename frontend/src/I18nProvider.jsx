import { useEffect, useState } from "react";
import { languages, translate } from "./locale";
import { LanguageContext } from "./i18n.js";

export function I18nProvider({ children }) {
  const [locale, setLocale] = useState(() => {
    try { const value = localStorage.getItem("busan-language"); return Object.hasOwn(languages, value) ? value : "ko"; }
    catch { return "ko"; }
  });
  useEffect(() => {
    document.documentElement.lang = locale;
    document.title = translate(locale, "pageTitle");
    try { localStorage.setItem("busan-language", locale); } catch { /* Browser storage can be disabled. */ }
  }, [locale]);
  return <LanguageContext.Provider value={{ locale, setLocale }}>{children}</LanguageContext.Provider>;
}
