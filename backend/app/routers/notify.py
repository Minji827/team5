import logging
import os
import smtplib
from email.mime.text import MIMEText
from typing import List, Optional

from dotenv import load_dotenv
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

load_dotenv()

router = APIRouter(prefix="/api/notify", tags=["notify"])
logger = logging.getLogger("notify")

GMAIL_ADDRESS = os.environ.get("GMAIL_ADDRESS")
GMAIL_APP_PASSWORD = os.environ.get("GMAIL_APP_PASSWORD")


class RouteStop(BaseModel):
    order: int
    name: str
    category: str
    address: str
    leg_minutes: Optional[float] = None
    duration_min: Optional[float] = None
    lat: Optional[float] = None
    lon: Optional[float] = None


class EmailRequest(BaseModel):
    email: str
    total_minutes: Optional[float] = None
    start_lat: Optional[float] = None
    start_lon: Optional[float] = None
    stops: List[RouteStop]


def build_google_maps_link(req: EmailRequest) -> Optional[str]:
    """출발지 -> 경유지들 -> 마지막 목적지를 도보 길찾기로 여는 구글맵 링크.
    좌표가 하나라도 빠지면(옛 클라이언트 등) 링크 없이 보낸다."""
    if req.start_lat is None or req.start_lon is None:
        return None
    if any(s.lat is None or s.lon is None for s in req.stops):
        return None

    origin = f"{req.start_lat},{req.start_lon}"
    destination = f"{req.stops[-1].lat},{req.stops[-1].lon}"
    waypoints = "|".join(f"{s.lat},{s.lon}" for s in req.stops[:-1])

    url = f"https://www.google.com/maps/dir/?api=1&origin={origin}&destination={destination}&travelmode=walking"
    if waypoints:
        url += f"&waypoints={waypoints}"
    return url


def build_email_body(req: EmailRequest) -> str:
    lines = [f"총 일정: {req.total_minutes}분 (체류 + 예상 도보 이동)", ""]
    for stop in req.stops:
        lines.append(f"{stop.order}. {stop.name} ({stop.category})")
        lines.append(f"   {stop.address}")
        if stop.leg_minutes is not None:
            lines.append(f"   이전 지점에서 도보 {stop.leg_minutes}분")
        if stop.duration_min is not None:
            lines.append(f"   체류 {stop.duration_min}분 (기본값)")
        lines.append("")

    maps_link = build_google_maps_link(req)
    if maps_link:
        lines.append(f"구글맵에서 전체 경로 보기: {maps_link}")
        lines.append("")

    lines.append("출처: 동백전 가맹점·한국관광공사·전통시장 데이터. 관광 방문지는 결제 확인 대상이 아니며, 가맹점도 현재 결제 가능 여부를 방문 전 확인해주세요.")
    return "\n".join(lines)


@router.post("/email")
def send_route_email(req: EmailRequest):
    if not GMAIL_ADDRESS or not GMAIL_APP_PASSWORD:
        logger.info("GMAIL_ADDRESS/GMAIL_APP_PASSWORD not set, skipping send to %s", req.email)
        return {"ok": True, "sent": False, "reason": "gmail credentials not configured yet"}

    msg = MIMEText(build_email_body(req))
    msg["Subject"] = "부산페이 도보 루트 추천"
    msg["From"] = GMAIL_ADDRESS
    msg["To"] = req.email

    try:
        with smtplib.SMTP_SSL("smtp.gmail.com", 465, timeout=10) as server:
            server.login(GMAIL_ADDRESS, GMAIL_APP_PASSWORD)
            server.sendmail(GMAIL_ADDRESS, [req.email], msg.as_string())
    except smtplib.SMTPException as e:
        logger.error("failed to send email via gmail smtp: %s", e)
        raise HTTPException(status_code=502, detail="이메일 전송에 실패했습니다.")

    return {"ok": True, "sent": True}
