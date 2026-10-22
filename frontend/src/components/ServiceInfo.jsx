import { useI18n } from "../i18n.js";
import Dialog from "./Dialog";

export default function ServiceInfo({ section, onClose }) {
  const { t } = useI18n();
  const privacy = section === "privacy";
  return <Dialog title={privacy ? t("privacy") : t("guideTitle")} onClose={onClose}>
    <div className="info-content">
      {privacy ? <>
        <h3>{t("privacyHeading1")}</h3><p>{t("privacyBody1")}</p>
        <h3>{t("privacyHeading2")}</h3><p>{t("privacyBody2")}</p>
        <h3>{t("privacyHeading3")}</h3><p>{t("privacyBody3")}</p>
        <p className="info-note">{t("privacyNote")}</p>
      </> : <>
        <p className="dialog-intro">{t("guideIntro")}</p>
        <ol className="guide-steps"><li><strong>{t("guideStep1")}</strong><p>{t("guideBody1")}</p></li><li><strong>{t("guideStep2")}</strong><p>{t("guideBody2")}</p></li><li><strong>{t("guideStep3")}</strong><p>{t("guideBody3")}</p></li></ol>
        <h3>{t("beforeVisit")}</h3><p>{t("beforeVisitBody")}</p>
      </>}
    </div>
    <button type="button" className="submit-btn" onClick={onClose}>{t("confirm")}</button>
  </Dialog>;
}
