import { useI18n } from "../i18n.js";
import { useEffect, useRef } from "react";
import Icon from "./Icon";

export default function Dialog({ title, children, onClose }) {
  const { t } = useI18n();
  const ref = useRef(null);
  useEffect(() => {
    const dialog = ref.current;
    dialog.showModal();
    return () => dialog.close();
  }, []);
  return (
    <dialog ref={ref} className="dialog" aria-labelledby="dialog-title" onCancel={onClose} onClick={(e) => { if (e.target === e.currentTarget) onClose(); }}>
      <div className="dialog-heading"><h2 id="dialog-title">{title}</h2><button type="button" className="icon-button" aria-label={t("close")} onClick={onClose}><Icon name="close" /></button></div>
      {children}
    </dialog>
  );
}
