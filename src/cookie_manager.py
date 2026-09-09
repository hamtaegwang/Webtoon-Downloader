# -*- coding: utf-8 -*-
"""
쿠키 관리 모듈
수동(직접) 입력 방식의 쿠키만을 처리하며, 세션에 적용합니다.
"""

import os
import re
import json
import requests


# 네이버 관련 도메인
NAVER_DOMAINS = [".naver.com", "comic.naver.com", "naver.com"]


class CookieManager:
    """수동으로 입력받은 쿠키를 파싱하여 세션에 적용하는 클래스"""

    def __init__(self):
        self.session = requests.Session()
        self.cookie_source = ""     # 쿠키를 가져온 출처
        self.is_loaded = False      # 쿠키 로드 성공 여부
        self._set_default_headers()

    def _set_default_headers(self):
        """
        네이버 웹툰에서 이미지/API를 정상적으로 받기 위한
        기본 HTTP 헤더를 설정합니다.
        """
        self.session.headers.update({
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/131.0.0.0 Safari/537.36"
            ),
            "Accept-Language": "ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
            "Referer": "https://comic.naver.com/",
        })

    # ─────────────────────────────────────────
    # 수동 입력
    # ─────────────────────────────────────────
    def load_from_string(self, cookie_str: str) -> tuple[bool, str]:
        """
        사용자가 직접 입력한 쿠키 문자열(Key=Value 혹은 JSON)을 파싱해 세션에 적용합니다.
        """
        if not cookie_str or not cookie_str.strip():
            return False, "쿠키 문자열이 비어 있습니다."
        
        cookies = {}
        cookie_str = cookie_str.strip()

        # 1. JSON 형식 시도 (셀레니움/확장 프로그램 내보내기 형식)
        if cookie_str.startswith("[") or cookie_str.startswith("{"):
            try:
                data = json.loads(cookie_str)
                if isinstance(data, list):
                    for item in data:
                        if isinstance(item, dict) and "name" in item and "value" in item:
                            cookies[item["name"]] = item["value"]
                elif isinstance(data, dict):
                    # dict 형태면 바로 업데이트 시도
                    cookies.update(data)
            except Exception:
                pass

        # 2. Key=Value 형식 시도 (세미콜론 구분)
        if not cookies:
            try:
                # 'Cookie:' 프리픽스 제거
                if cookie_str.lower().startswith("cookie:"):
                    cookie_str = cookie_str[7:].strip()
                
                for part in cookie_str.split(";"):
                    part = part.strip()
                    if "=" in part:
                        key, _, value = part.partition("=")
                        cookies[key.strip()] = value.strip()
            except Exception:
                pass

        if not cookies:
            return False, "쿠키를 파싱할 수 없습니다. JSON 혹은 'key=value;' 형식을 확인해 주세요."
        
        self.session.cookies.update(cookies)
        self._update_xsrf_token()
        self.cookie_source = "수동 입력"
        self.is_loaded = True
        return True, f"✅ 쿠키 {len(cookies)}개 적용 완료"

    def load_from_dict(self, cookies: dict, source: str = "자동 로그인") -> tuple[bool, str]:
        """
        딕셔너리 형태의 쿠키를 세션에 적용합니다. (셀레니움 연동용)
        """
        if not cookies:
            return False, "적용할 쿠키가 없습니다."
        
        self.session.cookies.update(cookies)
        self._update_xsrf_token()
        self.cookie_source = source
        self.is_loaded = True
        return True, f"✅ {source} 쿠키 {len(cookies)}개 적용 완료"

    def clear_cookies(self):
        """세션 쿠키를 초기화합니다."""
        self.session.cookies.clear()
        if "X-Xsrf-Token" in self.session.headers:
            del self.session.headers["X-Xsrf-Token"]
        self.cookie_source = ""
        self.is_loaded = False

    def _update_xsrf_token(self):
        """
        세션 쿠키 중 XSRF-TOKEN을 찾아 X-Xsrf-Token 헤더로 설정합니다.
        네이버 웹툰 API 호출 시 필수적인 경우가 많습니다.
        """
        token = self.session.cookies.get("XSRF-TOKEN")
        if token:
            self.session.headers.update({"X-Xsrf-Token": token})

    def get_status_text(self) -> str:
        """현재 쿠키 상태를 문자열로 반환합니다."""
        if self.is_loaded:
            return f"🔓 {self.cookie_source} 쿠키 적용됨"
        return "🔐 쿠키 없음 (성인/유료 회차 접근 불가)"
