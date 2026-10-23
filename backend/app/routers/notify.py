import json
from pathlib import Path
import logging
import os
import smtplib

import requests
from email.mime.text import MIMEText
from typing import List, Literal, Optional
from urllib.parse import urlencode

from dotenv import load_dotenv
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from app.services.place_labels import official_labels

load_dotenv()

router = APIRouter(prefix="/api/notify", tags=["notify"])
logger = logging.getLogger("notify")

EMAIL_COPY = json.loads((Path(__file__).resolve().parents[1] / "services/email_translations.json").read_text(encoding="utf-8"))

GMAIL_ADDRESS = os.environ.get("GMAIL_ADDRESS")
GMAIL_APP_PASSWORD = os.environ.get("GMAIL_APP_PASSWORD")


class RouteStop(BaseModel):
    id: Optional[str] = None
    order: int
    name: str
    category: str
    address: str
    leg_minutes: Optional[float] = None
    duration_min: Optional[float] = None
    lat: Optional[float] = None
    lon: Optional[float] = None


class EmailRequest(BaseModel):
    language: Literal["ko", "en", "ja", "zh-TW"] = "ko"
    email: str
    email_consent: bool = False
    return_to_start: bool = False
    return_minutes: Optional[float] = None
    total_minutes: Optional[float] = None
    max_minutes: int = Field(default=360, ge=30, le=360)
    start_label: Optional[str] = None
    start_lat: Optional[float] = None
    start_lon: Optional[float] = None
    stops: List[RouteStop]


def build_course_link(req: EmailRequest) -> Optional[str]:
    if not req.stops or req.start_lat is None or req.start_lon is None or any(not s.id for s in req.stops):
        return None
    params = {"start": f"{req.start_lat},{req.start_lon}", "stop": [s.id for s in req.stops],
              "minutes": req.max_minutes, "return": "1" if req.return_to_start else "0", "lang": req.language}
    if req.start_label:
        params["label"] = req.start_label
    site = os.environ.get("PUBLIC_SITE_URL", "https://busan-full-course.onrender.com").rstrip("/")
    return site + "/?" + urlencode(params, doseq=True)


def build_email_body(req: EmailRequest) -> str:
    text = EMAIL_COPY[req.language]
    lines = [text["total"].format(n=req.total_minutes), ""]
    missing_official = False
    for stop in req.stops:
        category = text["categories"].get(stop.category, stop.category)
        official = official_labels(stop, req.language)
        display_name = official.get("name") or stop.name
        display_address = official.get("address") or stop.address
        lines.append(f"{stop.order}. {display_name} ({category})")
        if display_name != stop.name:
            lines.append(f"   {text['native_name']}: {stop.name}")
        lines.append(f"   {text['address']}: {display_address}")
        if display_address != stop.address:
            lines.append(f"   {text['native_address']}: {stop.address}")
        if req.language != "ko" and (not official.get("name") or not official.get("address")):
            missing_official = True
        if stop.leg_minutes is not None:
            lines.append("   " + text["walk"].format(n=stop.leg_minutes))
        if stop.duration_min is not None:
            lines.append("   " + text["stay"].format(n=stop.duration_min))
        lines.append("")
    if req.return_to_start:
        lines.append(text["return"].format(n=req.return_minutes))
    course_link = build_course_link(req)
    if course_link:
        lines.extend([text["course_link"] + ": " + course_link, ""])
    if missing_official:
        lines.append(text["official_fallback"])
    lines.append(text["source"])
    return "\n".join(lines)


@router.post("/email")
def send_route_email(req: EmailRequest):
    if not req.email_consent:
        raise HTTPException(400, EMAIL_COPY[req.language]["consent"])
    if os.environ.get("EMAIL_DELIVERY_ENABLED", "true").lower() == "false":
        raise HTTPException(503, EMAIL_COPY[req.language]["error"])
    brevo_key = os.environ.get("BREVO_API_KEY")
    if brevo_key:
        sender = os.environ.get("EMAIL_FROM") or GMAIL_ADDRESS
        if not sender:
            raise HTTPException(503, EMAIL_COPY[req.language]["error"])
        try:
            response = requests.post(
                "https://api.brevo.com/v3/smtp/email",
                headers={"api-key": brevo_key, "accept": "application/json"},
                json={"sender": {"email": sender, "name": "Busan Full Course"},
                      "to": [{"email": req.email}],
                      "subject": EMAIL_COPY[req.language]["subject"],
                      "textContent": build_email_body(req)},
                timeout=15,
            )
            response.raise_for_status()
            if not response.json().get("messageId"):
                raise ValueError("Missing delivery acknowledgement")
        except (requests.RequestException, ValueError) as error:
            # Provider response bodies can contain recipient details; do not log them.
            logger.error("Brevo delivery failed: %s", type(error).__name__)
            raise HTTPException(502, EMAIL_COPY[req.language]["error"]) from None
        return {"ok": True, "sent": True}
    if not GMAIL_ADDRESS or not GMAIL_APP_PASSWORD:
        logger.info("Email sending is not configured; request skipped")
        return {"ok": True, "sent": False, "reason": "gmail credentials not configured yet"}

    msg = MIMEText(build_email_body(req))
    msg["Subject"] = EMAIL_COPY[req.language]["subject"]
    msg["From"] = GMAIL_ADDRESS
    msg["To"] = req.email

    try:
        with smtplib.SMTP_SSL("smtp.gmail.com", 465, timeout=10) as server:
            server.login(GMAIL_ADDRESS, GMAIL_APP_PASSWORD)
            server.sendmail(GMAIL_ADDRESS, [req.email], msg.as_string())
    except (smtplib.SMTPException, OSError) as e:
        logger.error("failed to send email via gmail smtp: %s", e)
        raise HTTPException(status_code=502, detail=EMAIL_COPY[req.language]["error"])

    return {"ok": True, "sent": True}
