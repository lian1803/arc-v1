"""
CRM 라우터 — 영업 CRM UI + API
GET  /crm                              — 대시보드
GET  /crm/business/{id}               — 채팅창
GET  /api/crm/businesses              — 업체 목록
GET  /api/crm/business/{id}           — 업체 상세
GET  /api/crm/business/{id}/chat      — 대화 기록 (없으면 1차 생성)
POST /api/crm/business/{id}/respond   — 고객 응답 + AI 답변
POST /api/crm/business/{id}/mark-sent — 발송 완료
GET  /api/crm/business/{id}/next-message — 다음 메시지
GET  /api/crm/business/{id}/pdf       — PDF 생성
GET  /api/crm/business/{id}/photo     — 진단 요약 사진
GET  /api/crm/business/{id}/place     — 네이버 플레이스 URL
POST /api/crm/business/{id}/update-package — 패키지 업데이트
"""
from __future__ import annotations

import os
import subprocess
import tempfile
from datetime import datetime, date, date as date_cls
from pathlib import Path
from typing import Optional

import importlib.util as _ilu

from fastapi import APIRouter, HTTPException, Depends, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update

from database import get_db
from models import CRMBusiness, CRMConversation, CRMMessageSequence, DiagnosisHistory
import services.crm_service as crm_svc

BASE_DIR = Path(__file__).parent.parent
templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))
router = APIRouter(tags=["crm"])

# Playwright PDF용 Python 경로 (company venv)
_COMPANY_PYTHON = str(BASE_DIR.parent.parent.parent.parent / "company" / "venv" / "Scripts" / "python.exe")
if not Path(_COMPANY_PYTHON).exists():
    _COMPANY_PYTHON = "python"  # fallback

# HtmlPdfGenerator 로드
try:
    _hp_spec = _ilu.spec_from_file_location("html_pdf_crm", str(BASE_DIR / "services" / "html_pdf_generator.py"))
    _hp_mod = _ilu.module_from_spec(_hp_spec)
    _hp_spec.loader.exec_module(_hp_mod)
    HtmlPdfGenerator = _hp_mod.HtmlPdfGenerator
    HTML_PDF_AVAILABLE = True
except Exception as _e:
    print(f"[CRM] HtmlPdfGenerator 로드 실패: {_e}")
    HTML_PDF_AVAILABLE = False

# 상태 전이 맵
STATUS_MAP = {
    '1차_발송_대기': '1차_발송_완료', '1차_발송_완료': '2차_생성',
    '2차_생성': '2차_발송_대기', '2차_발송_대기': '2차_발송_완료',
    '2차_발송_완료': '3차_생성', '3차_생성': '3차_발송_대기',
    '3차_발송_대기': '3차_발송_완료', '3차_발송_완료': '4차_생성',
    '4차_생성': '4차_발송_대기',
}
SENT_MAP = {
    '1차_발송_대기': '1차_발송_완료', '2차_발송_대기': '2차_발송_완료',
    '3차_발송_대기': '3차_발송_완료', '4차_발송_대기': '계약완료',
}

# ── Pydantic 모델 ────────────────────────────────────────────────────────────

class RespondRequest(BaseModel):
    message: str


class PackageUpdateRequest(BaseModel):
    package: str = "A"
    contract_status: str = "진단중"
    monthly_fee: Optional[int] = None
    manager: Optional[str] = None


# ── 내부 헬퍼 ────────────────────────────────────────────────────────────────

async def _get_business_or_404(db: AsyncSession, business_id: int) -> CRMBusiness:
    biz = await db.get(CRMBusiness, business_id)
    if not biz:
        raise HTTPException(status_code=404, detail="업체를 찾을 수 없습니다.")
    return biz


def _get_diagnosis_or_default(name: str, phone: str) -> dict:
    data = crm_svc.get_diagnosis_data_sync(name)
    if not data:
        data = crm_svc.get_default_diagnosis_data(name, phone or '')
    return data


# ── 페이지 라우트 ────────────────────────────────────────────────────────────

@router.get("/crm", response_class=HTMLResponse)
async def crm_dashboard(request: Request):
    return templates.TemplateResponse("crm_dashboard.html", {"request": request})


@router.get("/crm/business/{business_id}", response_class=HTMLResponse)
async def crm_chat_page(request: Request, business_id: int):
    return templates.TemplateResponse("crm_chat.html", {"request": request})


# ── API 라우트 ───────────────────────────────────────────────────────────────

@router.get("/api/crm/businesses")
async def get_crm_businesses(db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(CRMBusiness).order_by(CRMBusiness.created_at.desc())
    )
    businesses = result.scalars().all()
    return [b.to_dict() for b in businesses]


@router.get("/api/crm/business/{business_id}")
async def get_crm_business(business_id: int, db: AsyncSession = Depends(get_db)):
    biz = await _get_business_or_404(db, business_id)
    return biz.to_dict()


@router.get("/api/crm/business/{business_id}/chat")
async def get_crm_chat(business_id: int, db: AsyncSession = Depends(get_db)):
    biz = await _get_business_or_404(db, business_id)

    result = await db.execute(
        select(CRMConversation)
        .where(CRMConversation.business_id == business_id)
        .order_by(CRMConversation.created_at.asc())
    )
    messages = result.scalars().all()

    if not messages:
        # 1차 메시지 자동 생성
        first_msg = crm_svc.generate_crm_first_message(biz.name, biz.phone or '')
        conv = CRMConversation(
            business_id=business_id,
            speaker='AI',
            message=first_msg,
            message_order=1,
        )
        db.add(conv)
        # message_sequences에도 저장
        seq = CRMMessageSequence(
            business_id=business_id,
            sequence_num=1,
            message=first_msg,
        )
        db.add(seq)
        await db.commit()
        return [{"speaker": "AI", "message": first_msg, "created_at": conv.created_at.isoformat() if conv.created_at else None}]

    return [m.to_dict() for m in messages]


@router.post("/api/crm/business/{business_id}/respond")
async def crm_respond(
    business_id: int,
    body: RespondRequest,
    db: AsyncSession = Depends(get_db),
):
    if not body.message.strip():
        raise HTTPException(status_code=400, detail="메시지가 비어있습니다.")

    biz = await _get_business_or_404(db, business_id)

    # 고객 메시지 저장
    customer_conv = CRMConversation(
        business_id=business_id,
        speaker='고객',
        message=body.message,
    )
    db.add(customer_conv)
    await db.commit()

    # AI 응답 생성
    ai_response = crm_svc.generate_crm_response_messages(biz.name, biz.phone or '', body.message)

    # AI 응답 저장
    ai_conv = CRMConversation(
        business_id=business_id,
        speaker='AI',
        message=ai_response,
    )
    db.add(ai_conv)

    # 상태 전이
    next_status = STATUS_MAP.get(biz.status, biz.status)
    await db.execute(
        update(CRMBusiness)
        .where(CRMBusiness.id == business_id)
        .values(status=next_status)
    )
    await db.commit()

    return {"success": True, "ai_response": ai_response, "next_status": next_status}


@router.post("/api/crm/business/{business_id}/mark-sent")
async def crm_mark_sent(business_id: int, db: AsyncSession = Depends(get_db)):
    biz = await _get_business_or_404(db, business_id)

    next_status = SENT_MAP.get(biz.status)
    if not next_status:
        raise HTTPException(
            status_code=400,
            detail=f"이 상태에서는 발송 완료 처리할 수 없습니다: {biz.status}"
        )

    await db.execute(
        update(CRMBusiness).where(CRMBusiness.id == business_id).values(status=next_status)
    )
    await db.commit()
    return {"success": True, "next_status": next_status}


@router.get("/api/crm/business/{business_id}/next-message")
async def crm_next_message(business_id: int, db: AsyncSession = Depends(get_db)):
    biz = await _get_business_or_404(db, business_id)

    status_to_num = {'2차_생성': 2, '3차_생성': 3, '4차_생성': 4}
    message_num = status_to_num.get(biz.status)

    if not message_num:
        # 발송 대기 상태면 기존 시퀀스 반환
        waiting_to_num = {
            '2차_발송_대기': 2, '3차_발송_대기': 3, '4차_발송_대기': 4
        }
        message_num = waiting_to_num.get(biz.status)
        if not message_num:
            return {"success": True, "message": None, "info": "생성할 메시지가 없습니다. 고객 응답을 기다려주세요."}

    # 기존 시퀀스 조회
    result = await db.execute(
        select(CRMMessageSequence)
        .where(CRMMessageSequence.business_id == business_id)
        .where(CRMMessageSequence.sequence_num == message_num)
    )
    existing = result.scalar_one_or_none()
    if existing:
        return {"success": True, "message": existing.message, "message_num": message_num}

    # 새 메시지 생성
    ai_response = crm_svc.generate_crm_response_messages(biz.name, biz.phone or '', "")
    seq = CRMMessageSequence(
        business_id=business_id,
        sequence_num=message_num,
        message=ai_response,
    )
    db.add(seq)
    await db.commit()

    return {"success": True, "message": ai_response, "message_num": message_num}


@router.get("/api/crm/business/{business_id}/sales-manual")
async def crm_sales_manual(business_id: int, db: AsyncSession = Depends(get_db)):
    """업체별 전체 영업 매뉴얼 — AI 기획서 + 처방전 + 1~6차 메시지 전부"""
    biz = await _get_business_or_404(db, business_id)

    diagnosis_data = _get_diagnosis_or_default(biz.name, biz.phone or '')
    # CRMBusiness의 실제 주소(location)로 빈 address 채움
    if not diagnosis_data.get('address') and biz.location:
        diagnosis_data['address'] = biz.location

    # 1. AI 영업 기획서 생성 (신규)
    playbook = None
    try:
        from services.sales_strategist import get_or_generate_playbook
        playbook = get_or_generate_playbook(
            diagnosis_data,
            business_id=business_id,
            force_regenerate=False
        )
    except Exception as e:
        print(f"[CRM] AI 기획서 생성 실패: {e}")
        playbook = None

    # 2. 1~6차 메시지 전체 생성 (기존)
    messages = {}
    try:
        from services.message_generator import generate_all_messages
        all_msgs = generate_all_messages(diagnosis_data)

        messages['first'] = all_msgs.get('first', {})
        messages['second'] = all_msgs.get('second', '')
        messages['third'] = all_msgs.get('third', '')
        messages['fourth'] = all_msgs.get('fourth', {})
        messages['fifth'] = all_msgs.get('fifth', '')
        messages['sixth'] = all_msgs.get('sixth', '')
    except Exception as e:
        print(f"[CRM] 메시지 생성 실패: {e}")
        messages = {}

    # 3. 처방전 생성 (기존)
    prescription = None
    try:
        from services.prescription_generator import PrescriptionGenerator
        grade = diagnosis_data.get('grade', 'D')
        score = diagnosis_data.get('total_score', 0)
        weak_raw = diagnosis_data.get('improvement_points') or []
        if isinstance(weak_raw, str):
            import json as _json
            try:
                weak_raw = _json.loads(weak_raw)
            except Exception:
                weak_raw = []

        gen = PrescriptionGenerator()
        prescription = gen.generate(
            grade=grade,
            score=score,
            weak_items=weak_raw,
            business_name=biz.name,
            category=diagnosis_data.get('category', '소상공인'),
            data=diagnosis_data,
        )
    except Exception as e:
        print(f"[CRM] 처방전 생성 실패: {e}")
        prescription = None

    return {
        "business": biz.to_dict(),
        "playbook": playbook,  # 신규: AI 기획서
        "messages": messages,  # 기존: 템플릿 메시지 (하위 호환)
        "prescription": prescription,  # 기존: 처방전 (하위 호환)
    }


@router.get("/api/crm/business/{business_id}/pdf")
async def crm_download_pdf(business_id: int, db: AsyncSession = Depends(get_db)):
    biz = await _get_business_or_404(db, business_id)

    if not HTML_PDF_AVAILABLE:
        raise HTTPException(status_code=500, detail="HTML 생성 모듈 없음")

    name = biz.name
    phone = biz.phone or ''
    diagnosis_data = _get_diagnosis_or_default(name, phone)
    # CRMBusiness의 실제 주소(location)로 빈 address 채움
    if not diagnosis_data.get('address') and biz.location:
        diagnosis_data['address'] = biz.location
    addr = diagnosis_data.get('address', '')
    region = crm_svc.extract_region_from_address(addr) or os.environ.get('SALES_REGION', '')

    # HTML 렌더링
    generator = HtmlPdfGenerator()
    html = generator.render_html(diagnosis_data)

    folder_path, folder_name = crm_svc._get_business_folder(name, phone, region)
    pdf_path = os.path.join(folder_path, f"{folder_name}.pdf")
    tmp_html = os.path.join(folder_path, f"_tmp_{folder_name}.html")

    with open(tmp_html, 'w', encoding='utf-8') as f:
        f.write(html)

    file_uri = 'file:///' + tmp_html.replace('\\', '/')
    pdf_script = f'''
from playwright.sync_api import sync_playwright
with sync_playwright() as p:
    browser = p.chromium.launch()
    page = browser.new_page()
    page.goto("{file_uri}")
    page.wait_for_load_state("networkidle", timeout=15000)
    page.pdf(path=r"{pdf_path}", format="A4", print_background=True, margin={{"top":"0","right":"0","bottom":"0","left":"0"}})
    browser.close()
'''

    result = subprocess.run(
        [_COMPANY_PYTHON, '-c', pdf_script],
        capture_output=True, text=True, timeout=30
    )

    try:
        os.remove(tmp_html)
    except Exception:
        pass

    if result.returncode != 0:
        raise HTTPException(status_code=500, detail=f"PDF 생성 실패: {result.stderr[:200]}")

    return {"success": True, "message": "📋 PDF 저장 완료", "path": pdf_path, "folder": folder_path}


@router.get("/api/crm/business/{business_id}/photo")
async def crm_summary_photo(business_id: int, db: AsyncSession = Depends(get_db)):
    biz = await _get_business_or_404(db, business_id)

    name = biz.name
    phone = biz.phone or ''
    diagnosis_data = _get_diagnosis_or_default(name, phone)
    # CRMBusiness의 실제 주소(location)로 빈 address 채움
    if not diagnosis_data.get('address') and biz.location:
        diagnosis_data['address'] = biz.location
    addr = diagnosis_data.get('address', '')
    region = crm_svc.extract_region_from_address(addr) or os.environ.get('SALES_REGION', '')

    try:
        from PIL import Image, ImageDraw, ImageFont
        from io import BytesIO

        grade = diagnosis_data.get('grade', 'D')
        total_score = diagnosis_data.get('total_score', 0)
        review_count = diagnosis_data.get('review_count', 0)
        photo_count = diagnosis_data.get('photo_count', 0)
        competitor_avg_review = diagnosis_data.get('competitor_avg_review', 0)
        competitor_avg_photo = diagnosis_data.get('competitor_avg_photo', 0)
        estimated_lost = diagnosis_data.get('estimated_lost_customers', 0)
        rank = diagnosis_data.get('naver_place_rank', 0)

        grade_colors = {'A': '#00c73c', 'B': '#4caf50', 'C': '#ff9800', 'D': '#f44336'}
        grade_color = grade_colors.get(grade, '#f44336')
        bg_color = '#1a1a2e'
        card_color = '#16213e'
        text_color = '#ffffff'
        sub_color = '#a0a0a0'
        accent = '#e94560'

        try:
            font_large = ImageFont.truetype("malgun.ttf", 36)
            font_medium = ImageFont.truetype("malgun.ttf", 24)
            font_small = ImageFont.truetype("malgun.ttf", 18)
            font_grade = ImageFont.truetype("malgunbd.ttf", 72)
        except Exception:
            font_large = ImageFont.load_default()
            font_medium = font_large
            font_small = font_large
            font_grade = font_large

        cards = []
        cards.append(("현재 순위", f"{rank}위" if rank > 0 else "미확인", "검색 결과 노출 위치"))
        cards.append(("종합 점수", f"{total_score:.0f}점", f"{grade}등급"))
        if review_count > 0:
            desc = f"동네 평균 {competitor_avg_review}개" if competitor_avg_review > 0 else "리뷰 관리 필요"
            cards.append(("리뷰", f"{review_count}개", desc))
        if photo_count > 0:
            desc = f"동네 평균 {competitor_avg_photo}장" if competitor_avg_photo > 0 else "사진 관리 필요"
            cards.append(("사진", f"{photo_count}장", desc))
        else:
            cards.append(("사진", "등록 필요", "네이버 플레이스 사진 없음"))
        if estimated_lost > 0:
            avg_price = 60000
            annual_loss = estimated_lost * 12 * avg_price
            annual_loss_str = f"{annual_loss // 10000}만원" if annual_loss >= 10000 else f"{annual_loss:,}원"
            cards.append(("연간 기회손실", annual_loss_str, f"월 {estimated_lost}명 이탈 기준"))

        card_height = len(cards) * 140
        H = 160 + card_height + 100
        W = 800

        img = Image.new('RGB', (W, H), bg_color)
        draw = ImageDraw.Draw(img)

        draw.text((40, 30), "네이버 플레이스 진단", fill=sub_color, font=font_small)
        draw.text((40, 60), name, fill=text_color, font=font_large)

        cx, cy, r = 680, 80, 50
        draw.ellipse([cx-r, cy-r, cx+r, cy+r], fill=grade_color)
        bbox = draw.textbbox((0, 0), grade, font=font_grade)
        tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
        draw.text((cx - tw//2, cy - th//2 - 5), grade, fill='#fff', font=font_grade)

        draw.line([(40, 140), (W-40, 140)], fill='#333', width=2)

        y = 170
        for label, value, desc in cards:
            draw.rounded_rectangle([40, y, W-40, y+120], radius=12, fill=card_color)
            draw.text((70, y+15), label, fill=sub_color, font=font_small)
            draw.text((70, y+45), value, fill=accent, font=font_large)
            draw.text((70, y+88), desc, fill=sub_color, font=font_small)
            y += 140

        diag_date = diagnosis_data.get('created_at', '')[:10] if diagnosis_data.get('created_at') else date.today().isoformat()
        diag_id = f"DIAG-{diag_date.replace('-','')}-{business_id:04d}"
        draw.text((40, H-65), f"진단번호: {diag_id}", fill='#555', font=font_small)
        draw.text((40, H-40), f"수집일: {diag_date}  |  리안 컴퍼니", fill='#444', font=font_small)

        folder_path, folder_name = crm_svc._get_business_folder(name, phone, region)
        filename = f"{folder_name}_진단요약.png"
        filepath = os.path.join(folder_path, filename)
        img.save(filepath, format='PNG', quality=95)

        return {"success": True, "message": "📸 진단 사진 저장 완료", "path": filepath, "folder": folder_path}

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"이미지 생성 실패: {str(e)}")


@router.get("/api/crm/business/{business_id}/place")
async def crm_get_place(business_id: int, db: AsyncSession = Depends(get_db)):
    biz = await _get_business_or_404(db, business_id)

    place_url = biz.place_url
    if not place_url:
        diag = crm_svc.get_naver_diagnosis_by_name_sync(biz.name)
        if diag and diag.get('place_url'):
            place_url = diag['place_url']

    if not place_url:
        place_url = f"https://map.naver.com/p/search/{biz.name}"

    return {"place_url": place_url}


@router.post("/api/crm/business/{business_id}/update-package")
async def crm_update_package(
    business_id: int,
    body: PackageUpdateRequest,
    db: AsyncSession = Depends(get_db),
):
    await _get_business_or_404(db, business_id)

    fee_map = {'A': 380000, 'B': 560000, 'C': 950000}
    monthly_fee = body.monthly_fee if body.monthly_fee is not None else fee_map.get(body.package, 380000)

    await db.execute(
        update(CRMBusiness)
        .where(CRMBusiness.id == business_id)
        .values(
            package=body.package,
            contract_status=body.contract_status,
            monthly_fee=monthly_fee,
            manager=body.manager,
        )
    )
    await db.commit()

    return {
        "success": True,
        "message": "패키지 정보 업데이트 완료",
        "package": body.package,
        "contract_status": body.contract_status,
        "monthly_fee": monthly_fee,
        "manager": body.manager,
    }


# ── 2026-04-20 신규 API: 지역, 선택, 완료 ─────────────────────────────────────

@router.get("/api/crm/regions")
async def get_available_regions():
    """사용 가능한 지역 목록 반환"""
    regions = crm_svc.scan_available_regions()
    return {"regions": regions}


@router.get("/api/crm/region/{region}/businesses")
async def get_region_businesses(region: str, db: AsyncSession = Depends(get_db)):
    """지역별 업체 목록 조회 (엑셀 DB 자동 로드)"""
    try:
        businesses = await crm_svc.load_region_businesses_to_db(db, region)
        return {"region": region, "businesses": businesses, "count": len(businesses)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"지역 업체 로드 실패: {str(e)}")


@router.post("/api/crm/business/{business_id}/select-today")
async def toggle_select_today(business_id: int, db: AsyncSession = Depends(get_db)):
    """오늘 영업 선택 토글"""
    biz = await _get_business_or_404(db, business_id)
    new_value = not biz.today_selected

    await db.execute(
        update(CRMBusiness)
        .where(CRMBusiness.id == business_id)
        .values(today_selected=new_value)
    )
    await db.commit()

    return {"success": True, "today_selected": new_value}


@router.post("/api/crm/business/{business_id}/mark-contacted")
async def toggle_mark_contacted(business_id: int, db: AsyncSession = Depends(get_db)):
    """오늘 연락 완료 토글"""
    biz = await _get_business_or_404(db, business_id)
    new_value = not biz.contacted_today

    await db.execute(
        update(CRMBusiness)
        .where(CRMBusiness.id == business_id)
        .values(contacted_today=new_value)
    )
    await db.commit()

    return {"success": True, "contacted_today": new_value}


@router.post("/api/crm/reset-daily-flags")
async def reset_daily_flags(db: AsyncSession = Depends(get_db)):
    """자정 리셋 (매일 자동 호출)"""
    from datetime import date as date_cls
    today = date_cls.today()

    try:
        # 마지막 reset_date가 오늘이 아닌 모든 업체에 대해 리셋
        result = await db.execute(
            select(CRMBusiness).where(
                (CRMBusiness.last_reset_date < today) |
                (CRMBusiness.last_reset_date == None)
            )
        )
        businesses = result.scalars().all()

        for biz in businesses:
            biz.today_selected = False
            biz.contacted_today = False
            biz.last_reset_date = today

        await db.commit()
        return {"success": True, "reset_count": len(businesses)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"리셋 실패: {str(e)}")
