#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
온라인 마케팅 에이전시 제안서 자동 생성 시스템
diagnose() 결과 → HTML 렌더링 → 제안서 저장 → CRM 등록
"""

import sys
import json
from pathlib import Path
from datetime import datetime
from typing import Dict, Optional

# 경로 설정
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent.parent / "company"))

from online_brand_diagnosis import OnlineBrandDiagnosis

# CRM 모듈 import (같은 폴더)
try:
    from agency_crm import add_lead as crm_add_lead
    HAS_CRM = True
except ImportError:
    HAS_CRM = False

TEMPLATE_PATH = Path(__file__).parent.parent.parent.parent.parent / "company" / "html_templates" / "온라인마케팅에이전시_제안서.html"

PACKAGE_DESCRIPTIONS = {
    "Growth Starter": "퍼포먼스+SNS 기초 세팅 — 광고 학습 기간 3개월",
    "Growth Plus": "퍼포먼스+SNS+콘텐츠 동시 해결 — 구매 여정 전 단계 커버",
    "Full Stack": "5채널 통합+SEO+이커머스+IMC — 중견 브랜드 풀스펙",
}


def _html_to_pdf(html_content: str, output_path: str):
    """HTML을 PDF로 변환 (pdfkit/wkhtmltopdf 사용, 실패 시 HTML만 저장)."""
    output_path = str(output_path)

    try:
        import pdfkit
        options = {
            'page-size': 'A4',
            'margin-top': '0',
            'margin-right': '0',
            'margin-bottom': '0',
            'margin-left': '0',
            'encoding': "UTF-8",
            'no-outline': None,
            'enable-local-file-access': None,
        }
        pdfkit.from_string(html_content, output_path, options=options)
        return True
    except ImportError:
        # pdfkit 미설치 또는 wkhtmltopdf 없음
        return False
    except Exception as e:
        # PDF 생성 실패
        return False


def _render_with_jinja2(html_content: str, variables: Dict) -> str:
    """Jinja2를 사용한 템플릿 렌더링."""
    try:
        from jinja2 import Template
        template = Template(html_content)
        return template.render(**variables)
    except ImportError:
        # Jinja2 없으면 str.replace() 폴백
        print("⚠️  Jinja2 미설치, str.replace() 사용. 폴백 렌더링 중...")
        result = html_content
        for key, value in variables.items():
            result = result.replace(f"{{{{{key}}}}}", str(value))
        return result


def render_html(diagnosis_result: Dict, contact: str = "gonggu.l.1803@gmail.com") -> str:
    """
    진단 결과를 HTML 문자열로 렌더링 (PDF 변환 전 단계).

    Args:
        diagnosis_result: diagnose()의 반환값
        contact: 에이전시 연락처

    Returns:
        렌더링된 HTML 문자열
    """
    html_content = TEMPLATE_PATH.read_text(encoding="utf-8")

    breakdown = diagnosis_result.get("breakdown", {})
    problems = diagnosis_result.get("problems", [])

    # 변수 매핑
    variables = {
        "agency_name": "LIANCP 마케팅 에이전시",
        "brand_name": diagnosis_result.get("brand_name", "브랜드"),
        "contact": contact,
        "diagnosis_date": datetime.now().strftime("%Y-%m-%d"),
        "score": diagnosis_result.get("score", 0),
        "grade": diagnosis_result.get("grade", "D"),
        "perf_score": breakdown.get("퍼포먼스 광고", 0),
        "perf_score_percent": round(breakdown.get("퍼포먼스 광고", 0) / 30 * 100, 1) if breakdown.get("퍼포먼스 광고", 0) else 0,
        "sns_score": breakdown.get("SNS 운영", 0),
        "sns_score_percent": round(breakdown.get("SNS 운영", 0) / 25 * 100, 1) if breakdown.get("SNS 운영", 0) else 0,
        "ec_score": breakdown.get("이커머스 최적화", 0),
        "ec_score_percent": round(breakdown.get("이커머스 최적화", 0) / 25 * 100, 1) if breakdown.get("이커머스 최적화", 0) else 0,
        "seo_score": breakdown.get("SEO/콘텐츠", 0),
        "seo_score_percent": round(breakdown.get("SEO/콘텐츠", 0) / 20 * 100, 1) if breakdown.get("SEO/콘텐츠", 0) else 0,
        "problem_1": problems[0] if len(problems) > 0 else "추가 진단 필요",
        "problem_2": problems[1] if len(problems) > 1 else "추가 진단 필요",
        "problem_3": problems[2] if len(problems) > 2 else "추가 진단 필요",
        "recommended_package": diagnosis_result.get("recommended_package", "Growth Plus"),
        "package_price": diagnosis_result.get("package_price", "330만원"),
        "package_description": PACKAGE_DESCRIPTIONS.get(
            diagnosis_result.get("recommended_package", "Growth Plus"),
            ""
        ),
    }

    return _render_with_jinja2(html_content, variables)


def generate_pdf(
    diagnosis_result: Dict,
    output_path: str = "",
    contact: str = "gonggu.l.1803@gmail.com"
) -> str:
    """
    진단 결과 → HTML 렌더링 → PDF 저장.

    Args:
        diagnosis_result: diagnose()의 반환값
        output_path: PDF 저장 경로 (없으면 기본 경로에 자동 저장)
        contact: 에이전시 연락처

    Returns:
        생성된 PDF 파일의 절대 경로

    Raises:
        ValueError: 템플릿 파일이 없을 때
        Exception: HTML 렌더링 또는 PDF 변환 오류
    """
    if not TEMPLATE_PATH.exists():
        raise ValueError(f"템플릿 파일 없음: {TEMPLATE_PATH}")

    # 기본 저장 경로 설정
    if not output_path:
        brand_name = diagnosis_result.get("brand_name", "brand")
        proposals_dir = Path(__file__).parent.parent / "data" / "proposals"
        proposals_dir.mkdir(parents=True, exist_ok=True)

        date_str = datetime.now().strftime("%Y%m%d")
        output_path = proposals_dir / f"{brand_name}_{date_str}.pdf"

    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # HTML 렌더링
    html_content = render_html(diagnosis_result, contact)

    # PDF 생성 시도
    success = _html_to_pdf(html_content, str(output_path))

    # HTML 저장 (항상 실행)
    html_output = str(output_path).replace(".pdf", ".html")
    Path(html_output).write_text(html_content, encoding="utf-8")

    if success:
        print(f"✅ 제안서 생성 완료 (PDF)")
        print(f"📄 {output_path.absolute()}")
        return str(output_path.absolute())
    else:
        print(f"✅ 제안서 HTML 생성 완료")
        print(f"📄 {html_output}")
        print(f"\n💡 PDF 변환 방법:")
        print(f"   1. 브라우저에서 위 HTML 파일 열기")
        print(f"   2. Ctrl+P (또는 Cmd+P) → '다른 이름으로 PDF 저장'")
        return html_output


def register_to_crm(diagnosis_result: Dict, proposal_path: str, smartstore_url: str = "", insta_handle: str = "") -> Optional[str]:
    """
    제안서 생성 후 CRM에 자동 등록.

    Args:
        diagnosis_result: diagnose()의 반환값
        proposal_path: 생성된 제안서 경로
        smartstore_url: 스마트스토어 URL
        insta_handle: 인스타 핸들

    Returns:
        등록된 lead_id (성공 시) 또는 None (실패 시)
    """
    if not HAS_CRM:
        return None

    try:
        lead_id = crm_add_lead(
            brand_name=diagnosis_result["brand_name"],
            score=diagnosis_result["score"],
            grade=diagnosis_result["grade"],
            recommended_package=diagnosis_result["recommended_package"],
            smartstore_url=smartstore_url,
            insta_handle=insta_handle,
            notes=f"제안서 생성: {proposal_path}"
        )
        return lead_id
    except Exception as e:
        print(f"⚠️  CRM 등록 실패: {e}")
        return None


def main():
    """
    CLI: python proposal_generator.py 브랜드명 [스마트스토어URL] [인스타핸들]
    진단 → 제안서 생성 → CRM 등록까지 원스톱.
    """
    if len(sys.argv) < 2:
        print("사용법: python proposal_generator.py 브랜드명 [스마트스토어URL] [인스타핸들]")
        print("\n예시:")
        print("  python proposal_generator.py '브랜드명'")
        print("  python proposal_generator.py '브랜드명' 'https://smartstore.naver.com/xxx'")
        print("  python proposal_generator.py '브랜드명' 'https://smartstore.naver.com/xxx' 'brand_insta'")
        sys.exit(1)

    brand_name = sys.argv[1]
    smartstore_url = sys.argv[2] if len(sys.argv) > 2 else ""
    insta_handle = sys.argv[3] if len(sys.argv) > 3 else ""

    print(f"\n🔍 {brand_name} 온라인 마케팅 진단 중...")

    try:
        diagnosis = OnlineBrandDiagnosis()
        diagnosis_result = diagnosis.diagnose(brand_name, smartstore_url, insta_handle)

        print("\n" + diagnosis_result.get("report_text", ""))

        # 제안서 생성
        print("\n📝 제안서 생성 중...")
        proposal_path = generate_pdf(diagnosis_result)

        # CRM 등록
        print("\n📋 CRM 등록 중...")
        lead_id = register_to_crm(diagnosis_result, proposal_path, smartstore_url, insta_handle)
        if lead_id:
            print(f"✅ CRM 등록 완료 (ID: {lead_id})")
        else:
            print(f"⚠️  CRM 등록 건너뜀")

        # JSON 출력
        print("\n[진단 결과 JSON]")
        json_output = {
            "brand_name": diagnosis_result["brand_name"],
            "score": diagnosis_result["score"],
            "grade": diagnosis_result["grade"],
            "breakdown": diagnosis_result["breakdown"],
            "recommended_package": diagnosis_result["recommended_package"],
            "package_price": diagnosis_result["package_price"],
            "proposal_path": proposal_path,
            "lead_id": lead_id,
        }
        print(json.dumps(json_output, ensure_ascii=False, indent=2))

    except Exception as e:
        print(f"\n❌ 오류: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
