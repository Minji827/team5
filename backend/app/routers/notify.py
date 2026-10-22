import json
from pathlib import Path
import logging
import os
import smtplib

import requests
from email.mime.text import MIMEText
from typing import List, Literal, Optional

from dotenv import load_dotenv
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
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
    start_lat: Optional[float] = None
    start_lon: Optional[float] = None
    stops: List[RouteStop]


def build_google_maps_link(req: EmailRequest) -> Optional[str]:
    """출발지 -> 경유지들 -> 마지막 목적지를 도보 길찾기로 여는 구글맵 링크.
    좌표가 하나라도 빠지면(옛 클라이언트 등) 링크 없이 보낸다."""
    if not req.stops or req.start_lat is None or req.start_lon is None:
        return None
    if any(s.lat is None or s.lon is None for s in req.stops):
        return None

    origin = f"{req.start_lat},{req.start_lon}"
    destination = origin if req.return_to_start else f"{req.stops[-1].lat},{req.stops[-1].lon}"
    waypoints = "|".join(f"{s.lat},{s.lon}" for s in (req.stops if req.return_to_start else req.stops[:-1]))

    url = f"https://www.google.com/maps/dir/?api=1&origin={origin}&destination={destination}&travelmode=walking"
    if waypoints:
        url += f"&waypoints={waypoints}"
    return url


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
    maps_link = build_google_maps_link(req)
    if maps_link:
        lines.extend([text["maps"] + ": " + maps_link, ""])
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
