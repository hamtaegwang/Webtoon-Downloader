# -*- coding: utf-8 -*-
"""
Webtoon Downloader - Core API Module
네이버 웹툰(정식 웹툰, 베스트 도전, 도전만화) 스크래핑 및 다운로드 모듈
"""

import os
import re
import time
import json
import requests
import concurrent.futures
from bs4 import BeautifulSoup
from urllib.parse import urlparse, parse_qs
from typing import Optional, Callable, Dict, Any, List


# ─────────────────────────────────────────────
# Custom Exception Hierarchy
# ─────────────────────────────────────────────
class WebtoonError(Exception):
    """웹툰 스크래퍼 기본 예외 클래스"""
    pass


class RatingError(WebtoonError):
    """성인 인증 쿠키가 필요할 때 발생하는 예외"""
    pass


class WebtoonNotFoundError(WebtoonError):
    """존재하지 않는 웹툰 ID이거나 삭제된 웹툰일 때 발생하는 예외"""
    pass


class EpisodeNotFoundError(WebtoonError):
    """회차가 존재하지 않거나 유료/대여/삭제 회차일 때 발생하는 예외"""
    pass


class URLError(WebtoonError):
    """지원하지 않거나 잘못된 웹툰 URL 형식일 때 발생하는 예외"""
    pass


# ─────────────────────────────────────────────
# Constants & Headers
# ─────────────────────────────────────────────
NAVER_COMIC_BASE = "https://comic.naver.com"
WEBTOON_LIST_API = "https://comic.naver.com/api/article/list"
WEBTOON_INFO_API = "https://comic.naver.com/api/article/list/info"

DEFAULT_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/131.0.0.0 Safari/537.36 Edg/131.0.0.0"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
    "Accept-Language": "ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7",
    "Referer": "https://comic.naver.com/webtoon",
    "sec-ch-ua": '"Not;A=Brand";v="99", "Chromium";v="131", "Microsoft Edge";v="131"',
    "sec-ch-ua-mobile": "?0",
    "sec-ch-ua-platform": '"Windows"',
    "service-ticket-id": "comic_webtoon",
    "service-type": "KW",
}

COMMENT_HEADERS = {
    "Accept": "*/*",
    "Accept-Language": "ko",
    "Connection": "keep-alive",
    "Referer": "https://comic.naver.com/",
    "Sec-Fetch-Dest": "empty",
    "Sec-Fetch-Mode": "cors",
    "Sec-Fetch-Site": "same-origin",
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/131.0.0.0 Safari/537.36 Edg/131.0.0.0"
    ),
    "language": "KOREAN",
    "sec-ch-ua": '"Not;A=Brand";v="99", "Microsoft Edge";v="131", "Chromium";v="131"',
    "sec-ch-ua-mobile": "?0",
    "sec-ch-ua-platform": '"Windows"',
    "service-ticket-id": "comic_webtoon",
    "service-type": "KW",
}


# ─────────────────────────────────────────────
# URL Parsing & Identification
# ─────────────────────────────────────────────
def extract_title_id(url: str, session: Optional[requests.Session] = None) -> Optional[str]:
    """
    다양한 형태의 네이버 웹툰 URL에서 titleId를 추출합니다.
    - https://comic.naver.com/webtoon/list?titleId=12345
    - https://comic.naver.com/bestChallenge/list?titleId=12345
    - https://comic.naver.com/challenge/list?titleId=12345
    - https://m.comic.naver.com/...
    - https://naver.me/... (단축 공유 링크 추적)
    """
    if not url or not url.strip():
        return None

    url = url.strip()

    # 1. naver.me 단축 공유 링크인 경우 원본 URL로 리다이렉트 추적
    if "naver.me" in url:
        try:
            s = session or requests.Session()
            resp = s.get(url, headers=DEFAULT_HEADERS, allow_redirects=True, timeout=10)
            url = resp.url
        except Exception:
            pass

    parsed = urlparse(url)
    params = parse_qs(parsed.query)

    # 2. query param에 titleId가 있는 경우
    if "titleId" in params and params["titleId"]:
        return params["titleId"][0]

    # 3. URL path에 포함된 경우
    match = re.search(r'titleId=(\d+)', url)
    if match:
        return match.group(1)

    match = re.search(r'/(?:webtoon|bestChallenge|challenge)/(?:list|detail)/(\d+)', url)
    if match:
        return match.group(1)

    return None


def resolve_webtoon_type(level_code: str) -> str:
    """
    네이버 웹툰 API의 webtoonLevelCode를 웹툰 경로명으로 매핑합니다.
    - WEBTOON -> webtoon (정식 연재)
    - BEST_CHALLENGE -> bestChallenge (베스트 도전)
    - CHALLENGE -> challenge (도전만화)
    """
    code = (level_code or "").upper()
    if "BEST" in code:
        return "bestChallenge"
    elif "CHALLENGE" in code:
        return "challenge"
    return "webtoon"


# ─────────────────────────────────────────────
# Webtoon Information API
# ─────────────────────────────────────────────
def get_webtoon_info(session: requests.Session, title_id: str) -> Dict[str, Any]:
    """
    웹툰 메타데이터(제목, 작가, 썸네일, 시놉시스, 장르, 웹툰 분류, 성인 등급 등)를 수집합니다.
    """
    try:
        headers = dict(DEFAULT_HEADERS)
        resp = session.get(WEBTOON_INFO_API, params={"titleId": title_id}, headers=headers, timeout=15)
        
        if resp.status_code in (404, 500):
            raise WebtoonNotFoundError(f"존재하지 않거나 삭제된 웹툰입니다. (titleId: {title_id})")
        
        resp.raise_for_status()
        data = resp.json()

        # 성인 등급(19금) 및 연령 등급 확인
        age_info = data.get("age", {})
        age_type = age_info.get("type", "RATE_ALL") if isinstance(age_info, dict) else "RATE_ALL"
        
        # 작가 목록 파싱
        artists = data.get("communityArtists", [])
        author = ", ".join(a.get("name", "") for a in artists if a.get("name")) or "Unknown"

        # 썸네일 (긴 비율 sharedThumbnailUrl 또는 일반 thumbnailUrl)
        thumbnail = data.get("sharedThumbnailUrl") or data.get("thumbnailUrl") or data.get("posterThumbnailUrl") or ""

        # 장르 목록 파싱
        genres_list = data.get("genres", [])
        genre = ", ".join(g.get("description", "") for g in genres_list if g.get("description")) or "미분류"

        # 웹툰 타입 코드 확인 (WEBTOON / BEST_CHALLENGE / CHALLENGE)
        level_code = data.get("webtoonLevelCode", "WEBTOON")
        webtoon_type = resolve_webtoon_type(level_code)

        title_name = data.get("titleName", "No Title")

        return {
            "titleId": str(title_id),
            "titleName": title_name,
            "author": author,
            "thumbnail": thumbnail,
            "synopsis": data.get("synopsis", ""),
            "finish": data.get("finished", False),
            "genre": genre,
            "webtoon_type": webtoon_type,              # 'webtoon', 'bestChallenge', 'challenge'
            "webtoon_level_code": level_code,
            "age_type": age_type,                      # 'RATE_ALL', 'RATE_12', 'RATE_15', 'RATE_18'
            "totalEpisodeCount": data.get("totalArticleCount", 0),
        }
    except WebtoonError:
        raise
    except requests.HTTPError as e:
        if e.response is not None and e.response.status_code in (401, 403):
            raise RatingError("성인 인증 쿠키가 필요하거나 접근 권한이 없습니다. 상단에서 로그인을 진행해주세요.")
        raise WebtoonError(f"웹툰 정보를 가져오지 못했습니다: {e}")
    except Exception as e:
        raise WebtoonError(f"웹툰 정보를 가져오는 중 오류 발생: {e}")


# ─────────────────────────────────────────────
# Episode List API
# ─────────────────────────────────────────────
def get_all_episodes(
    session: requests.Session,
    title_id: str,
    progress_callback: Optional[Callable[[int, int], None]] = None
) -> List[Dict[str, Any]]:
    """
    모든 회차 목록을 수집합니다.
    - 검수 중(blindInspection) 회차 제외
    - 유료/미리보기(charge) 회차 감지
    - 대량 페이지 고속 병렬 수집 지원
    - 페이지 끝 감지 및 Gap(누락 회차) 보정 인덱싱
    """
    episodes: List[Dict[str, Any]] = []
    headers = dict(DEFAULT_HEADERS)
    page = 1

    try:
        resp = session.get(
            WEBTOON_LIST_API,
            params={"titleId": title_id, "page": page, "sort": "ASC"},
            headers=headers,
            timeout=15
        )

        if resp.status_code == 404:
            raise WebtoonNotFoundError(f"존재하지 않는 웹툰입니다. (titleId: {title_id})")
        elif resp.status_code in (401, 403):
            raise RatingError("성인 인증 쿠키가 필요합니다. 상단에서 로그인을 진행해주세요.")
        elif resp.status_code != 200:
            raise WebtoonError(f"서버 응답 오류 (HTTP {resp.status_code})")

        data = resp.json()
    except WebtoonError:
        raise
    except Exception as e:
        raise WebtoonError(f"회차 목록을 가져오는 중 오류 발생: {str(e)}")

    total_pages = data.get("pageInfo", {}).get("totalPages", 1)
    _parse_episode_page(data, episodes)

    if progress_callback:
        progress_callback(1, total_pages)

    # 2페이지 이상일 경우 병렬로 빠르게 수집 (중복/끝 페이지 방어 로직 포함)
    if total_pages > 1:
        def fetch_single_page(p: int):
            try:
                r = session.get(
                    WEBTOON_LIST_API,
                    params={"titleId": title_id, "page": p, "sort": "ASC"},
                    headers=headers,
                    timeout=15
                )
                if r.status_code == 200:
                    return p, r.json()
            except Exception:
                pass
            return p, None

        page_results: Dict[int, dict] = {}
        completed_count = 1

        with concurrent.futures.ThreadPoolExecutor(max_workers=min(10, total_pages)) as executor:
            future_to_page = {
                executor.submit(fetch_single_page, p): p for p in range(2, total_pages + 1)
            }
            for future in concurrent.futures.as_completed(future_to_page):
                p, p_data = future.result()
                if p_data:
                    page_results[p] = p_data
                completed_count += 1
                if progress_callback:
                    progress_callback(completed_count, total_pages)

        # 페이지 순서대로 병합
        previous_article_ids = {ep["no"] for ep in episodes}
        for p in range(2, total_pages + 1):
            if p in page_results:
                page_episodes: list = []
                _parse_episode_page(page_results[p], page_episodes)
                # 이전 페이지와 중복되는 데이터 방어
                new_episodes = [e for e in page_episodes if e["no"] not in previous_article_ids]
                for e in new_episodes:
                    episodes.append(e)
                    previous_article_ids.add(e["no"])

    # 회차 번호(no) 기준 오름차순 정렬 (Gap이 있어도 순서 보장)
    episodes.sort(key=lambda x: x["no"])
    return episodes


def _parse_episode_page(data: dict, episodes: list):
    """API 응답 데이터에서 회차 정보를 파싱하여 episodes 리스트에 추가합니다."""
    for item in data.get("articleList", []):
        # 검수/블라인드 처리된 회차는 제외
        if item.get("blindInspection", False):
            continue

        ep_no = item.get("no", 0)
        is_charged = item.get("charge", False)
        subtitle = item.get("subtitle", f"{ep_no}화")

        episodes.append({
            "no": ep_no,
            "title": subtitle,
            "date": item.get("serviceDateDescription", ""),
            "thumbnail": item.get("thumbnailUrl", ""),
            "is_charged": is_charged,
        })


# ─────────────────────────────────────────────
# Episode Detail, Images & Author Words Extraction
# ─────────────────────────────────────────────
def get_episode_data(
    session: requests.Session,
    title_id: str,
    episode_no: int,
    webtoon_type: str = "webtoon",
) -> Dict[str, Any]:
    """
    회차 페이지에서 본문 이미지 URL 목록, BGM 오디오 URL, 작가의 말을 단 1회의 GET 요청으로 고속 파싱합니다.
    """
    path_name = "webtoon"
    if "best" in webtoon_type.lower():
        path_name = "bestChallenge"
        image_selector = "#comic_view_area > div > img, #comic_view_area img"
    elif "challenge" in webtoon_type.lower():
        path_name = "challenge"
        image_selector = "#comic_view_area > div > img, #comic_view_area img"
    else:
        path_name = "webtoon"
        image_selector = "#sectionContWide > img, #sectionContWide img"

    base_url = f"https://comic.naver.com/{path_name}"
    url = f"{base_url}/detail?titleId={title_id}&no={episode_no}"

    headers = dict(DEFAULT_HEADERS)
    headers["Referer"] = f"{base_url}/list?titleId={title_id}"

    image_urls: List[str] = []
    audio_url: Optional[str] = None
    author_words: str = ""

    try:
        resp = session.get(url, headers=headers, timeout=15)
        resp.raise_for_status()
        html = resp.text
        soup = BeautifulSoup(html, "html.parser")

        # ── 1. BGM 오디오 URL 추출 ──
        try:
            audio_source = soup.select_one("audio#bgmPlayer > source, audio > source, audio#bgmPlayer")
            if audio_source:
                src = audio_source.get("src")
                if src and src.strip():
                    audio_url = src.strip()
        except Exception:
            pass

        # ── 2. 작가의 말 (authorWords) 추출 ──
        try:
            search_result = re.search(r'"authorWords"\s*:\s*"(.*?)"', html)
            if search_result:
                raw_words = search_result.group(1)
                try:
                    author_words = json.loads(f'"{raw_words}"')
                except Exception:
                    author_words = raw_words
                author_words = author_words.strip()
        except Exception:
            pass

        # ── 3. DOM 셀렉터를 통한 본문 이미지 추출 (가장 정확 & 차단 없음) ──
        found_elements = soup.select(image_selector)
        if not found_elements:
            found_elements = soup.select(
                "#sectionContWide img, #comic_view_area img, .wt_viewer img, .view_area img, img[id^='content_image_']"
            )

        for el in found_elements:
            src = el.get("src") or el.get("data-src")
            if not src:
                continue
            src = src.strip()

            # 배너/안내 이미지 제외
            if any(banner in src for banner in ["agerate", "ctguide", "nthumbnail", "nstore", "center-pf"]):
                continue

            if src not in image_urls:
                image_urls.append(src)

        # ── 4. JSON 데이터 파싱 폴백 (__state__ 또는 __NEXT_DATA__) ──
        if not image_urls:
            state_match = re.search(r'window\.__state__\s*=\s*(\{.*?\});', html, re.DOTALL)
            if state_match:
                try:
                    state_data = json.loads(state_match.group(1))
                    json_urls = (
                        state_data.get("article", {})
                        .get("view", {})
                        .get("content", {})
                        .get("imageUrlList", [])
                    )
                    if json_urls:
                        image_urls = [u for u in json_urls if u]
                    if not author_words:
                        author_words = state_data.get("article", {}).get("authorWords", "")
                except Exception:
                    pass

        # ── 5. 모바일 페이지 폴백 ──
        if not image_urls:
            try:
                m_headers = dict(DEFAULT_HEADERS)
                m_headers.update({
                    "User-Agent": (
                        "Mozilla/5.0 (Linux; Android 10; K) "
                        "AppleWebKit/537.36 (KHTML, like Gecko) "
                        "Chrome/131.0.0.0 Mobile Safari/537.36"
                    ),
                    "Referer": f"https://m.comic.naver.com/{path_name}/list?titleId={title_id}"
                })
                m_url = f"https://m.comic.naver.com/{path_name}/detail?titleId={title_id}&no={episode_no}"
                m_resp = session.get(m_url, headers=m_headers, timeout=10)
                if m_resp.status_code == 200:
                    m_html = m_resp.text
                    next_data_match = re.search(
                        r'<script id="__NEXT_DATA__" type="application/json">(.*?)</script>',
                        m_html,
                        re.DOTALL
                    )
                    if next_data_match:
                        m_data = json.loads(next_data_match.group(1))
                        m_article = (
                            m_data.get("props", {})
                            .get("pageProps", {})
                            .get("initialInitData", {})
                            .get("article", {})
                        )
                        m_urls = (
                            m_article.get("view", {})
                            .get("content", {})
                            .get("imageUrlList", [])
                        )
                        if m_urls:
                            image_urls = [u for u in m_urls if u]
                        if not author_words:
                            author_words = m_article.get("authorWords", "")
            except Exception:
                pass

    except requests.HTTPError as e:
        if e.response is not None and e.response.status_code in (401, 403):
            raise RatingError(f"{episode_no}화: 유료 회차이거나 성인 인증이 필요합니다.")
        raise EpisodeNotFoundError(f"{episode_no}화 페이지 로드 실패: {e}")
    except WebtoonError:
        raise
    except Exception as e:
        raise EpisodeNotFoundError(f"{episode_no}화 추출 중 오류 발생: {e}")

    if not image_urls:
        raise EpisodeNotFoundError(f"{episode_no}화: 이미지를 찾을 수 없습니다. (유료/대여 회차이거나 삭제된 회차)")

    return {
        "images": image_urls,
        "audio": audio_url,
        "author_words": author_words,
    }


def get_episode_images(
    session: requests.Session,
    title_id: str,
    episode_no: int,
    webtoon_type: str = "webtoon",
    executor: Optional[concurrent.futures.ThreadPoolExecutor] = None,
) -> List[str]:
    """기존 코드와의 호환성을 유지하기 위한 래퍼 함수."""
    data = get_episode_data(session, title_id, episode_no, webtoon_type=webtoon_type)
    return data["images"]


# ─────────────────────────────────────────────
# Episode Comments API
# ─────────────────────────────────────────────
def get_episode_comments(
    session: requests.Session,
    title_id: str,
    episode_no: int,
    sort: str = "favorite",
    limit: int = 15
) -> List[Dict[str, Any]]:
    """
    회차의 베스트 댓글 또는 최신 댓글을 수집합니다.
    (실패 시 빈 리스트 []를 반환하여 전체 다운로드 프로세스에 영향을 주지 않음)
    """
    comments: List[Dict[str, Any]] = []
    try:
        url = "https://apis.naver.com/commentBox/cbox/web_naver_list_json.json"
        params = {
            "ticket": "comic",
            "templateId": "webtoon",
            "pool": "cbox",
            "lang": "ko",
            "country": "KR",
            "objectId": f"{title_id}_{episode_no}",
            "pageSize": limit,
            "page": 1,
            "sort": sort,
        }
        headers = dict(COMMENT_HEADERS)
        headers["Referer"] = f"https://comic.naver.com/webtoon/detail?titleId={title_id}&no={episode_no}"

        resp = session.get(url, params=params, headers=headers, timeout=5)
        if resp.status_code == 200:
            data = resp.json()
            if data.get("success"):
                raw_comments = data.get("result", {}).get("commentList", [])
                for c in raw_comments:
                    comments.append({
                        "userName": c.get("userName") or c.get("maskedUserId") or "익명",
                        "contents": c.get("contents", ""),
                        "regTime": c.get("regTimeGmt", "")[:10] if c.get("regTimeGmt") else "",
                        "sympathyCount": c.get("sympathyCount", 0),
                        "antipathyCount": c.get("antipathyCount", 0),
                    })
    except Exception:
        pass
    return comments


# ─────────────────────────────────────────────
# Downloader Functions
# ─────────────────────────────────────────────
def download_image(
    session: requests.Session,
    url: str,
    save_path: str,
    title_id: str,
    max_retries: int = 5
) -> bool:
    """
    웹툰 컷 이미지를 스트림으로 다운로드합니다.
    """
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/131.0.0.0 Safari/537.36"
        ),
        "Referer": f"https://comic.naver.com/webtoon/list?titleId={title_id}",
        "Sec-Fetch-Dest": "image",
        "Sec-Fetch-Mode": "no-cors",
        "Sec-Fetch-Site": "cross-site",
        "Accept": "image/avif,image/webp,image/apng,image/svg+xml,image/*,*/*;q=0.8",
    }

    for i in range(max_retries):
        try:
            r = session.get(url, headers=headers, timeout=30, stream=True)
            r.raise_for_status()
            with open(save_path, "wb") as f:
                for chunk in r.iter_content(chunk_size=16384):
                    if chunk:
                        f.write(chunk)
            return True
        except Exception:
            if i < max_retries - 1:
                time.sleep(1.5 ** i)
            continue
    return False


def download_audio(
    session: requests.Session,
    url: str,
    save_path: str,
    max_retries: int = 5
) -> bool:
    """
    웹툰 BGM 효과음/배경음악(.mp3) 파일을 다운로드합니다.
    """
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/131.0.0.0 Safari/537.36"
        ),
        "Referer": "https://comic.naver.com/",
        "Sec-Fetch-Dest": "audio",
        "Sec-Fetch-Mode": "no-cors",
        "Sec-Fetch-Site": "cross-site",
    }

    for i in range(max_retries):
        try:
            r = session.get(url, headers=headers, timeout=30, stream=True)
            r.raise_for_status()
            with open(save_path, "wb") as f:
                for chunk in r.iter_content(chunk_size=16384):
                    if chunk:
                        f.write(chunk)
            return True
        except Exception:
            if i < max_retries - 1:
                time.sleep(1.5 ** i)
            continue
    return False


def download_thumbnail(session: requests.Session, url: str, save_path: str) -> bool:
    """웹툰 대표 썸네일/포스터 이미지를 다운로드합니다."""
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/131.0.0.0 Safari/537.36"
        ),
        "Referer": "https://comic.naver.com/",
    }
    try:
        r = session.get(url, headers=headers, timeout=15)
        r.raise_for_status()
        with open(save_path, "wb") as f:
            f.write(r.content)
        return True
    except Exception:
        return False

