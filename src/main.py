# -*- coding: utf-8 -*-
"""
Webtoon Downloader - 메인 GUI
tkinter 기반 윈도우 애플리케이션
"""

import os
import sys
import json
import threading
import concurrent.futures
import webbrowser
import requests
import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext
from io import BytesIO
from PIL import Image, ImageTk
import time

# 셀레니움 관련
try:
    from selenium import webdriver
    from selenium.webdriver.chrome.service import Service
    from selenium.webdriver.chrome.options import Options
    from selenium.common.exceptions import WebDriverException, NoSuchWindowException
    from webdriver_manager.chrome import ChromeDriverManager
    HAS_SELENIUM = True
except ImportError:
    HAS_SELENIUM = False

# 실행 환경에 따른 경로 설정 (PyInstaller 지원)
def get_resource_path(relative_path):
    """실행 파일로 빌드된 경우와 일반 파이썬 실행 환경 모두에서 리소스를 올바르게 찾습니다."""
    if getattr(sys, 'frozen', False) and hasattr(sys, '_MEIPASS'):
        # PyInstaller에 의해 압축 해제된 임시 폴더 경로
        return os.path.join(sys._MEIPASS, relative_path)
    # 일반 실행 시: src/main.py 기준 상위 폴더(루트)에서 경로 탐색
    return os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), relative_path)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from webtoon_api import (
    extract_title_id,
    get_webtoon_info,
    get_all_episodes,
    get_episode_images,
    get_episode_data,
    get_episode_comments,
    download_image,
    download_audio,
    download_thumbnail,
    WebtoonError,
    RatingError,
    WebtoonNotFoundError,
    EpisodeNotFoundError,
    URLError,
)
from cookie_manager import CookieManager
from utils import make_episode_folder, make_webtoon_folder, sanitize_filename
from html_generator import generate_viewer


# ─────────────────────────────────────────────
# 애플리케이션 버전 및 정보
# ─────────────────────────────────────────────
APP_VERSION = "1.0.4"
APP_AUTHOR = "제작 : RubyKor"
VERSION_CHECK_URL = "https://raw.githubusercontent.com/hamtaegwang/Webtoon-Downloader/main/version.json"
DOWNLOAD_URL = "https://rubykor.tistory.com/3"


# ─────────────────────────────────────────────
# 색상 및 폰트 상수
# ─────────────────────────────────────────────
BG_COLOR = "#1e1e2e"          # 메인 배경 (다크)
SURFACE_COLOR = "#2a2a3e"     # 카드/패널 배경
ACCENT_COLOR = "#03c75a"      # 브랜드 색상 (Accent Green)
ACCENT_HOVER = "#02a84a"      # 강조색 호버
TEXT_COLOR = "#e0e0e0"        # 기본 텍스트
SUBTEXT_COLOR = "#a0a0b0"     # 보조 텍스트
BORDER_COLOR = "#3a3a5a"      # 테두리색
ERROR_COLOR = "#ff6b6b"       # 오류색
WARNING_COLOR = "#ffd93d"     # 경고색

FONT_MAIN = ("맑은 고딕", 10)
FONT_BOLD = ("맑은 고딕", 10, "bold")
FONT_TITLE = ("맑은 고딕", 14, "bold")
FONT_SUBTITLE = ("맑은 고딕", 11, "bold")
FONT_SMALL = ("맑은 고딕", 9)
FONT_MONO = ("Consolas", 9)


class WebtoonDownloader(tk.Tk):
    """메인 애플리케이션 윈도우"""

    def __init__(self):
        super().__init__()
        self.title("Webtoon Downloader")
        self.geometry("920x780")
        self.minsize(800, 680)
        self.configure(bg=BG_COLOR)

        # 아이콘 설정 (assets 폴더에 icon.ico 및 icon.png 사용)
        icon_ico_path = get_resource_path(os.path.join("assets", "icon.ico"))
        icon_png_path = get_resource_path(os.path.join("assets", "icon.png"))

        # 윈도우 High DPI 인식 설정 및 AppUserModelID 설정
        if sys.platform == "win32":
            try:
                import ctypes
                # DPI Awareness 설정 (Windows 8.1 이상 추천 방식)
                # 0: Unaware, 1: System Aware, 2: Per Monitor Aware
                ctypes.windll.shcore.SetProcessDpiAwareness(1)
                
                # 작업표시줄 아이콘 그룹화 및 아이콘 표시를 위한 ID 설정
                myappid = 'webtoon.downloader.v1'
                ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(myappid)
            except Exception:
                # 구버전 윈도우용 폴백
                try:
                    ctypes.windll.user32.SetProcessDPIAware()
                except Exception:
                    pass

        # 아이콘 설정 우선순위:
        # 1. iconphoto: 타 OS 호환성 및 작업표시줄 아이콘용
        # 2. iconbitmap: 윈도우 타이틀바에 가장 적합 (멀티 사이즈 ico 사용)
        if os.path.exists(icon_png_path):
            try:
                icon_image = Image.open(icon_png_path)
                # 안티앨리어싱 효과를 극대화하기 위해 LANCZOS 사용
                # 윈도우는 여러 크기를 넘겨주면 시스템이 최적의 것을 선택함
                icon_16 = ImageTk.PhotoImage(icon_image.resize((16, 16), Image.LANCZOS))
                icon_32 = ImageTk.PhotoImage(icon_image.resize((32, 32), Image.LANCZOS))
                icon_48 = ImageTk.PhotoImage(icon_image.resize((48, 48), Image.LANCZOS))
                self.icon_photo_list = [icon_48, icon_32, icon_16]  # 참조 유지
                self.iconphoto(True, *self.icon_photo_list)
            except Exception:
                pass

        if os.path.exists(icon_ico_path):
            try:
                # 윈도우 전용: iconbitmap이 가장 깔끔하게 보여질 가능성이 큼 (iconphoto 이후에 호출하여 덮어쓰기)
                if sys.platform == "win32":
                    self.iconbitmap(icon_ico_path)
            except Exception:
                pass

        # 쿠키 매니저 초기화
        self.cookie_mgr = CookieManager()
        self.session = self.cookie_mgr.session

        # 내부 상태
        self.current_title_id = None
        self.current_webtoon_info = None
        self.all_episodes = []
        self.thumbnail_photo = None   # tkinter PhotoImage 참조 보관 (GC 방지)
        self.logo_photo = None        # 로고 이미지 레퍼런스
        
        # 설정 파일 경로 및 저장 경로 초기화
        self.config_path = self._get_config_path()
        self.save_path = self._load_save_path()
        self.is_downloading = False
        self._lock = threading.Lock()  # 대기열 및 상태 제어를 위한 스레드 락
        self.download_queue = []  # 다운로드 대기열 [(info, episodes, save_path), ...]

        # UI 구성
        self._build_ui()
        
        # 버전 체크 (비동기 수행)
        threading.Thread(target=self._check_version, daemon=True).start()

        # 면책 조항 팝업 표시 (메인 윈도우 렌더링 후 중앙 배치를 위해 약간의 지연)
        self.after(200, self._show_disclaimer)

    def _get_config_path(self):
        """
        설정 파일(config.json)의 경로를 반환합니다.
        기존에 실행 파일 경로에 생성되던 파일을 시스템 AppData(숨김 폴더)로 이전하여 깔끔하게 유지합니다.
        """
        if getattr(sys, 'frozen', False):
            old_base_dir = os.path.dirname(sys.executable)
        else:
            old_base_dir = os.path.dirname(BASE_DIR)
        old_config_path = os.path.join(old_base_dir, "config.json")

        # 새 경로 (AppData) 설정
        app_data_dir = os.getenv('APPDATA')
        if not app_data_dir:
            app_data_dir = os.path.expanduser("~")
            
        new_config_dir = os.path.join(app_data_dir, "Webtoon Downloader")
        if not os.path.exists(new_config_dir):
            try:
                os.makedirs(new_config_dir, exist_ok=True)
            except Exception:
                pass
                
        new_config_path = os.path.join(new_config_dir, "config.json")

        # 기존 설정 파일이 실행 파일 옆에 존재하고 새 설정 파일은 없다면 자동 마이그레이션(이동)
        if os.path.exists(old_config_path) and not os.path.exists(new_config_path):
            try:
                import shutil
                shutil.move(old_config_path, new_config_path)
            except Exception:
                pass
                
        # 새 경로(AppData)를 사용 가능하면 반환, 아니면 이전 경로 폴백
        if os.path.exists(new_config_dir):
            return new_config_path
        return old_config_path

    def _load_save_path(self):
        """
        설정 파일에서 이전에 지정한 저장 경로를 불러옵니다.
        설정이 없거나 경로가 유효하지 않으면 기본 경로를 반환합니다.
        """
        default_path = os.path.join(os.path.expanduser("~"), "Downloads", "웹툰")
        if os.path.exists(self.config_path):
            try:
                with open(self.config_path, "r", encoding="utf-8") as f:
                    config = json.load(f)
                    saved = config.get("save_path", "")
                    if saved and os.path.exists(saved):
                        return saved
            except Exception:
                pass
        return default_path

    def _save_config(self):
        """현재 저장 경로를 config.json 파일에 안전하게 저장합니다."""
        try:
            with open(self.config_path, "w", encoding="utf-8") as f:
                json.dump({"save_path": self.save_path}, f, ensure_ascii=False, indent=4)
        except Exception:
            pass

    # ───────────────────────────────────────────
    # UI 빌드
    # ───────────────────────────────────────────
    def _build_ui(self):
        """전체 UI를 생성합니다."""
        # ── 상단 헤더 (공통) ──
        self._build_header()

        # ── 커스텀 다크 테마 탭 바 (Segmented Tab Bar) ──
        tab_bar = tk.Frame(self, bg=BG_COLOR)
        tab_bar.pack(fill="x", padx=10, pady=(8, 4))

        self.current_active_tab = "search"

        # 1. 웹툰 검색 탭 버튼
        self.btn_search_tab = tk.Button(
            tab_bar,
            text="🔍  웹툰 검색",
            font=("맑은 고딕", 11, "bold"),
            bg=ACCENT_COLOR,
            fg="#ffffff",
            activebackground=ACCENT_HOVER,
            activeforeground="#ffffff",
            relief="flat",
            cursor="hand2",
            padx=24,
            pady=8,
            bd=0,
            command=lambda: self._switch_tab("search")
        )
        self.btn_search_tab.pack(side="left", padx=(0, 6))

        # 2. 대기열 관리 탭 버튼
        self.btn_queue_tab = tk.Button(
            tab_bar,
            text="📋  대기열 관리",
            font=("맑은 고딕", 11, "bold"),
            bg=SURFACE_COLOR,
            fg=SUBTEXT_COLOR,
            activebackground="#383852",
            activeforeground="#ffffff",
            relief="flat",
            cursor="hand2",
            padx=24,
            pady=8,
            bd=0,
            command=lambda: self._switch_tab("queue")
        )
        self.btn_queue_tab.pack(side="left")

        # 탭 호버 효과 바인딩
        self.btn_search_tab.bind("<Enter>", lambda e: self._on_tab_hover(self.btn_search_tab, "search", True))
        self.btn_search_tab.bind("<Leave>", lambda e: self._on_tab_hover(self.btn_search_tab, "search", False))
        self.btn_queue_tab.bind("<Enter>", lambda e: self._on_tab_hover(self.btn_queue_tab, "queue", True))
        self.btn_queue_tab.bind("<Leave>", lambda e: self._on_tab_hover(self.btn_queue_tab, "queue", False))

        # ── 탭 콘텐츠 컨테이너 ──
        self.tab_container = tk.Frame(self, bg=BG_COLOR)
        self.tab_container.pack(fill="both", expand=True, padx=10, pady=(0, 5))

        # 1. 웹툰 검색 탭 콘텐츠
        self.search_tab = tk.Frame(self.tab_container, bg=BG_COLOR)
        self.search_tab.pack(fill="both", expand=True)
        self._build_search_tab_ui()

        # 2. 대기열 관리 탭 콘텐츠
        self.queue_tab = tk.Frame(self.tab_container, bg=BG_COLOR)
        self._build_queue_tab_ui()

        # ── 진행률 + 로그 (공통) ──
        self._build_progress_panel()

    def _switch_tab(self, tab_name: str):
        """탭을 전환합니다."""
        self.current_active_tab = tab_name
        if tab_name == "search":
            self.btn_search_tab.config(bg=ACCENT_COLOR, fg="#ffffff", activebackground=ACCENT_HOVER, activeforeground="#ffffff")
            self.btn_queue_tab.config(bg=SURFACE_COLOR, fg=SUBTEXT_COLOR, activebackground="#383852", activeforeground="#ffffff")
            self.search_tab.pack(fill="both", expand=True)
            self.queue_tab.pack_forget()
        else:
            self.btn_queue_tab.config(bg=ACCENT_COLOR, fg="#ffffff", activebackground=ACCENT_HOVER, activeforeground="#ffffff")
            self.btn_search_tab.config(bg=SURFACE_COLOR, fg=SUBTEXT_COLOR, activebackground="#383852", activeforeground="#ffffff")
            self.queue_tab.pack(fill="both", expand=True)
            self.search_tab.pack_forget()

    def _on_tab_hover(self, btn: tk.Button, tab_name: str, entering: bool):
        """탭 마우스 호버 효과"""
        if self.current_active_tab != tab_name:
            if entering:
                btn.config(bg="#383852", fg="#ffffff")
            else:
                btn.config(bg=SURFACE_COLOR, fg=SUBTEXT_COLOR)

    def _build_search_tab_ui(self):
        """웹툰 검색 및 회차 선택 탭 UI 구성"""
        # URL 입력 영역
        self._build_url_bar(self.search_tab)
        # 웹툰 정보 패널
        self._build_info_panel(self.search_tab)
        # 회차 목록 + 버튼 영역
        self._build_episode_panel(self.search_tab)

    def _build_header(self):
        """앱 제목 헤더"""
        header = tk.Frame(self, bg=SURFACE_COLOR, height=50)
        header.pack(fill="x", side="top")
        header.pack_propagate(False)

        # 로고 이미지 로드 (assets/icon.png)
        logo_path = get_resource_path(os.path.join("assets", "icon.png"))
        if os.path.exists(logo_path):
            try:
                logo_img = Image.open(logo_path)
                logo_img.thumbnail((32, 32), Image.LANCZOS)
                self.logo_photo = ImageTk.PhotoImage(logo_img)
                tk.Label(
                    header,
                    image=self.logo_photo,
                    bg=SURFACE_COLOR
                ).pack(side="left", padx=(18, 0), pady=12)
            except Exception:
                pass

        tk.Label(
            header,
            text="Webtoon Downloader",
            font=FONT_TITLE,
            bg=SURFACE_COLOR,
            fg=ACCENT_COLOR,
        ).pack(side="left", padx=(8, 4), pady=12)

        # 제작 및 버전 정보 추가
        tk.Label(
            header,
            text=f"v{APP_VERSION} | {APP_AUTHOR}",
            font=FONT_SMALL,
            bg=SURFACE_COLOR,
            fg=SUBTEXT_COLOR,
        ).pack(side="left", padx=(0, 18), pady=(16, 12))

        # 쿠키 상태 레이블
        self.cookie_status_var = tk.StringVar(value="🔐 로그인이 필요할 수 있습니다.")
        self.cookie_label = tk.Label(
            header,
            textvariable=self.cookie_status_var,
            font=FONT_SMALL,
            bg=SURFACE_COLOR,
            fg=SUBTEXT_COLOR,
        )
        self.cookie_label.pack(side="right", padx=14)

        # 쿠키 수동 입력 버튼
        tk.Button(
            header,
            text="직접 입력",
            font=FONT_SMALL,
            bg=BORDER_COLOR,
            fg=TEXT_COLOR,
            activebackground=ACCENT_COLOR,
            activeforeground="#fff",
            relief="flat",
            cursor="hand2",
            command=self._open_cookie_dialog,
        ).pack(side="right", padx=2)

        # 자동 로그인 버튼 추가
        tk.Button(
            header,
            text="자동 로그인",
            font=FONT_SMALL,
            bg=SURFACE_COLOR,
            fg=ACCENT_COLOR,
            activebackground=ACCENT_HOVER,
            activeforeground="#fff",
            relief="flat",
            cursor="hand2",
            command=self._run_auto_login,
        ).pack(side="right", padx=2)

    def _build_url_bar(self, parent):
        """URL 입력창 영역"""
        bar = tk.Frame(parent, bg=BG_COLOR, pady=10)
        bar.pack(fill="x", padx=14)

        tk.Label(bar, text="웹툰 URL", font=FONT_BOLD, bg=BG_COLOR, fg=TEXT_COLOR).pack(
            side="left"
        )

        self.url_var = tk.StringVar()
        self.url_entry = tk.Entry(
            bar,
            textvariable=self.url_var,
            font=FONT_MAIN,
            bg=SURFACE_COLOR,
            fg=TEXT_COLOR,
            insertbackground=TEXT_COLOR,
            relief="flat",
            bd=6,
        )
        self.url_entry.pack(side="left", fill="x", expand=True, padx=8)
        self.url_entry.bind("<Return>", lambda e: self._load_webtoon())

        # 저장 경로 버튼
        tk.Button(
            bar,
            text="📁 저장 경로",
            font=FONT_MAIN,
            bg=SURFACE_COLOR,
            fg=TEXT_COLOR,
            activebackground=BORDER_COLOR,
            relief="flat",
            cursor="hand2",
            command=self._choose_save_path,
        ).pack(side="right", padx=(4, 0))

        # 불러오기 버튼
        self.load_btn = tk.Button(
            bar,
            text="🔍 불러오기",
            font=FONT_BOLD,
            bg=ACCENT_COLOR,
            fg="#fff",
            activebackground=ACCENT_HOVER,
            activeforeground="#fff",
            relief="flat",
            cursor="hand2",
            padx=10,
            command=self._load_webtoon,
        )
        self.load_btn.pack(side="right", padx=4)

        # 현재 저장 경로 표시
        self.save_path_var = tk.StringVar(value=f"저장 경로: {self.save_path}")
        tk.Label(
            parent,
            textvariable=self.save_path_var,
            font=FONT_SMALL,
            bg=BG_COLOR,
            fg=SUBTEXT_COLOR,
            anchor="w",
        ).pack(fill="x", padx=20, pady=(0, 4))

    def _build_info_panel(self, parent):
        """웹툰 정보(썸네일 + 텍스트 정보) 패널"""
        self.info_frame = tk.Frame(parent, bg=SURFACE_COLOR, bd=0)
        self.info_frame.pack(fill="x", padx=14, pady=(0, 8))

        # 썸네일 영역 (왼쪽)
        self.thumb_frame = tk.Frame(self.info_frame, bg=SURFACE_COLOR, width=120, height=160)
        self.thumb_frame.pack(side="left", padx=12, pady=12)
        self.thumb_frame.pack_propagate(False)

        self.thumb_label = tk.Label(
            self.thumb_frame,
            text="🖼",
            font=("Segoe UI", 32),
            bg=SURFACE_COLOR,
            fg=BORDER_COLOR,
        )
        self.thumb_label.pack(fill="both", expand=True)

        # 텍스트 정보 영역 (오른쪽)
        info_text_frame = tk.Frame(self.info_frame, bg=SURFACE_COLOR)
        info_text_frame.pack(side="left", fill="both", expand=True, padx=(0, 12), pady=12)

        self.webtoon_title_var = tk.StringVar(value="웹툰 URL을 입력하고 불러오기를 눌러주세요.")
        tk.Label(
            info_text_frame,
            textvariable=self.webtoon_title_var,
            font=FONT_TITLE,
            bg=SURFACE_COLOR,
            fg=TEXT_COLOR,
            anchor="w",
            wraplength=600,
            justify="left",
        ).pack(fill="x", pady=(0, 4))

        self.author_var = tk.StringVar(value="")
        tk.Label(
            info_text_frame,
            textvariable=self.author_var,
            font=FONT_MAIN,
            bg=SURFACE_COLOR,
            fg=SUBTEXT_COLOR,
            anchor="w",
        ).pack(fill="x")

        self.genre_var = tk.StringVar(value="")
        tk.Label(
            info_text_frame,
            textvariable=self.genre_var,
            font=FONT_MAIN,
            bg=SURFACE_COLOR,
            fg=SUBTEXT_COLOR,
            anchor="w",
        ).pack(fill="x")

        self.synopsis_var = tk.StringVar(value="")
        tk.Label(
            info_text_frame,
            textvariable=self.synopsis_var,
            font=FONT_SMALL,
            bg=SURFACE_COLOR,
            fg=SUBTEXT_COLOR,
            anchor="w",
            wraplength=600,
            justify="left",
        ).pack(fill="x", pady=(6, 0))

    def _build_episode_panel(self, parent):
        """회차 목록 + 버튼 영역"""
        outer = tk.Frame(parent, bg=BG_COLOR)
        outer.pack(fill="both", expand=True, padx=14, pady=(0, 6))

        # ── 헤더 (전체선택/해제 + 총 회차 수) ──
        ep_header = tk.Frame(outer, bg=BG_COLOR)
        ep_header.pack(fill="x", pady=(0, 4))

        self.ep_count_var = tk.StringVar(value="회차 목록")
        tk.Label(
            ep_header,
            textvariable=self.ep_count_var,
            font=FONT_SUBTITLE,
            bg=BG_COLOR,
            fg=TEXT_COLOR,
        ).pack(side="left")

        # ── 정렬 순서 토글 ──
        self.sort_desc_var = tk.BooleanVar(value=True)
        tk.Checkbutton(
            ep_header,
            text="최신순",
            variable=self.sort_desc_var,
            font=FONT_SMALL,
            bg=BG_COLOR,
            fg=SUBTEXT_COLOR,
            selectcolor=SURFACE_COLOR,
            activebackground=BG_COLOR,
            command=self._sort_episodes,
        ).pack(side="left", padx=10)

        # ── 버튼 그룹 (오른쪽) ──
        btn_frame = tk.Frame(ep_header, bg=BG_COLOR)
        btn_frame.pack(side="right")

        for text, cmd in [
            ("전체 선택", self._select_all),
            ("전체 해제", self._deselect_all),
        ]:
            tk.Button(
                btn_frame,
                text=text,
                font=FONT_SMALL,
                bg=SURFACE_COLOR,
                fg=TEXT_COLOR,
                activebackground=BORDER_COLOR,
                relief="flat",
                cursor="hand2",
                padx=8,
                command=cmd,
            ).pack(side="left", padx=2)

        self.download_btn = tk.Button(
            btn_frame,
            text="⬇  즉시 다운로드",
            font=FONT_BOLD,
            bg=ACCENT_COLOR,
            fg="#fff",
            activebackground=ACCENT_HOVER,
            activeforeground="#fff",
            relief="flat",
            cursor="hand2",
            padx=12,
            command=self._start_download,
        )
        self.download_btn.pack(side="left", padx=4)

        self.add_queue_btn = tk.Button(
            btn_frame,
            text="+ 대기열 추가",
            font=FONT_BOLD,
            bg=SURFACE_COLOR,
            fg=TEXT_COLOR,
            activebackground=BORDER_COLOR,
            relief="flat",
            cursor="hand2",
            padx=10,
            command=self._add_to_queue,
        )
        self.add_queue_btn.pack(side="left", padx=2)

        # ── 회차 목록 (Listbox + 스크롤바) ──
        list_frame = tk.Frame(outer, bg=SURFACE_COLOR, bd=1, relief="flat")
        list_frame.pack(fill="both", expand=True)

        scrollbar = tk.Scrollbar(list_frame, bg=SURFACE_COLOR, troughcolor=BG_COLOR)
        scrollbar.pack(side="right", fill="y")

        self.episode_listbox = tk.Listbox(
            list_frame,
            font=FONT_MAIN,
            bg=SURFACE_COLOR,
            fg=TEXT_COLOR,
            selectbackground=ACCENT_COLOR,
            selectforeground="#fff",
            activestyle="none",
            relief="flat",
            bd=0,
            highlightthickness=0,
            selectmode="extended",       # Ctrl/Shift 다중 선택 지원
            yscrollcommand=scrollbar.set,
        )
        self.episode_listbox.pack(side="left", fill="both", expand=True, padx=4, pady=4)
        scrollbar.config(command=self.episode_listbox.yview)

    def _build_queue_tab_ui(self):
        """대기열 관리 탭 UI 구성"""
        outer = tk.Frame(self.queue_tab, bg=BG_COLOR)
        outer.pack(fill="both", expand=True, padx=20, pady=15)

        # ── 헤더 ──
        header = tk.Frame(outer, bg=BG_COLOR)
        header.pack(fill="x", pady=(0, 10))

        tk.Label(
            header,
            text="📥 다운로드 대기열",
            font=FONT_SUBTITLE,
            bg=BG_COLOR,
            fg=TEXT_COLOR,
        ).pack(side="left")

        # ── 버튼 그룹 ──
        btn_frame = tk.Frame(header, bg=BG_COLOR)
        btn_frame.pack(side="right")

        tk.Button(
            btn_frame,
            text="선택 삭제",
            font=FONT_SMALL,
            bg=SURFACE_COLOR,
            fg=ERROR_COLOR,
            activebackground=BORDER_COLOR,
            relief="flat",
            cursor="hand2",
            padx=8,
            command=self._remove_from_queue,
        ).pack(side="left", padx=4)

        self.start_queue_btn = tk.Button(
            btn_frame,
            text="🚀 전체 다운로드 시작",
            font=FONT_BOLD,
            bg=ACCENT_COLOR,
            fg="#fff",
            activebackground=ACCENT_HOVER,
            relief="flat",
            cursor="hand2",
            padx=15,
            command=self._start_queue_download,
        )
        self.start_queue_btn.pack(side="left", padx=(10, 0))

        # ── 대기열 목록 ──
        list_frame = tk.Frame(outer, bg=SURFACE_COLOR, bd=1, relief="flat")
        list_frame.pack(fill="both", expand=True)

        q_scrollbar = tk.Scrollbar(list_frame, bg=SURFACE_COLOR)
        q_scrollbar.pack(side="right", fill="y")

        self.queue_listbox = tk.Listbox(
            list_frame,
            font=FONT_MAIN,
            bg=SURFACE_COLOR,
            fg=TEXT_COLOR,
            selectbackground=ACCENT_COLOR,
            selectforeground="#fff",
            relief="flat",
            bd=0,
            highlightthickness=0,
            yscrollcommand=q_scrollbar.set,
        )
        self.queue_listbox.pack(side="left", fill="both", expand=True, padx=5, pady=5)
        q_scrollbar.config(command=self.queue_listbox.yview)

    def _build_progress_panel(self):
        """진행률 바 + 로그 출력 영역"""
        prog_frame = tk.Frame(self, bg=BG_COLOR)
        prog_frame.pack(fill="x", padx=14, pady=(0, 4))

        self.progress_var = tk.DoubleVar(value=0)
        self.progress_label_var = tk.StringVar(value="대기 중")

        tk.Label(
            prog_frame,
            textvariable=self.progress_label_var,
            font=FONT_SMALL,
            bg=BG_COLOR,
            fg=SUBTEXT_COLOR,
        ).pack(anchor="w")

        style = ttk.Style()
        style.theme_use("default")
        style.configure(
            "Green.Horizontal.TProgressbar",
            troughcolor=SURFACE_COLOR,
            background=ACCENT_COLOR,
            thickness=14,
        )

        self.progressbar = ttk.Progressbar(
            prog_frame,
            variable=self.progress_var,
            maximum=100,
            style="Green.Horizontal.TProgressbar",
        )
        self.progressbar.pack(fill="x", pady=4)

        # 로그 출력 (스크롤 텍스트)
        self.log_text = scrolledtext.ScrolledText(
            self,
            height=7,
            font=FONT_MONO,
            bg=SURFACE_COLOR,
            fg=TEXT_COLOR,
            insertbackground=TEXT_COLOR,
            relief="flat",
            bd=0,
            state="disabled",
        )
        self.log_text.pack(fill="both", expand=True, padx=14, pady=(0, 10))

        # 에러 태그 설정 (한 번만 수행하도록 최적화)
        self.log_text.tag_config("error", foreground=ERROR_COLOR)

    # ───────────────────────────────────────────
    # 쿠키 관련
    # ───────────────────────────────────────────
    def _update_cookie_status(self, success: bool, msg: str):
        """쿠키 상태 레이블을 업데이트합니다."""
        self.cookie_status_var.set(msg)
        self.cookie_label.config(fg=ACCENT_COLOR if success else WARNING_COLOR)

    def _open_cookie_dialog(self):
        """쿠키 수동 입력 다이얼로그를 엽니다."""
        dialog = tk.Toplevel(self)
        dialog.title("쿠키 직접 입력")
        dialog.geometry("560x250")
        dialog.configure(bg=BG_COLOR)
        dialog.transient(self)
        dialog.grab_set()

        tk.Label(
            dialog,
            text="[수동 쿠키 획득 및 입력 방법]\n"
                 "• 방법 A: 브라우저 개발자 도구(F12) -> Network -> Headers -> 'cookie:' 값 복사\n"
                 "• 방법 B: 'Get cookies.txt' 확장 프로그램 등으로 추출한 JSON/Netscape 텍스트 복사\n"
                 "• 위에서 복사한 내용을 아래 칸에 그대로 붙여넣고 [적용]을 눌러주세요.",
            font=FONT_SMALL,
            bg=BG_COLOR,
            fg=SUBTEXT_COLOR,
            justify="left",
            padx=16
        ).pack(pady=(12, 8), anchor="w")

        cookie_text = scrolledtext.ScrolledText(
            dialog,
            height=5,
            font=FONT_MONO,
            bg=SURFACE_COLOR,
            fg=TEXT_COLOR,
            insertbackground=TEXT_COLOR,
            relief="flat",
        )
        cookie_text.pack(fill="both", expand=True, padx=16)

        def apply_cookie():
            raw = cookie_text.get("1.0", "end").strip()
            success, msg = self.cookie_mgr.load_from_string(raw)
            self._update_cookie_status(success, msg)
            if success:
                dialog.destroy()
            else:
                messagebox.showerror("오류", msg, parent=dialog)

        tk.Button(
            dialog,
            text="적용",
            font=FONT_BOLD,
            bg=ACCENT_COLOR,
            fg="#fff",
            relief="flat",
            cursor="hand2",
            command=apply_cookie,
        ).pack(pady=10)

    # ───────────────────────────────────────────
    # 셀레니움 자동 로그인
    # ───────────────────────────────────────────
    def _run_auto_login(self):
        """셀레니움을 이용해 네이버 로그인을 시도하고 쿠키를 가져옵니다."""
        if not HAS_SELENIUM:
            messagebox.showerror(
                "라이브러리 부족",
                "셀레니움 라이브러리가 설치되지 않았습니다.\n'pip install selenium webdriver-manager' 명령어로 설치해주세요.",
                parent=self
            )
            return

        self._log("🌐 자동 로그인 브라우저를 실행하는 중...")
        threading.Thread(target=self._selenium_login_worker, daemon=True).start()

    def _selenium_login_worker(self):
        """백그라운드 스레드: 셀레니움 브라우저 제어 및 로그인 감지"""
        driver = None
        try:
            # 크롬 옵션 설정
            chrome_options = Options()
            chrome_options.add_argument("--window-size=400,700")  # 작은 창 크기
            chrome_options.add_argument("--mute-audio")
            # 필요 시 유저 데이터 폴더를 지정하여 기존 세션 유지 가능 (여기서는 깔끔하게 매번 로그인)
            
            # 드라이버 서비스 설정 (자동 매니저 사용)
            service = Service(ChromeDriverManager().install())
            driver = webdriver.Chrome(service=service, options=chrome_options)
            
            driver.get("https://nid.naver.com/nidlogin.login")
            self.after(0, lambda: self._log("🔑 네이버 로그인 창이 열렸습니다. 로그인을 진행해주세요."))

            # 로그인 감지 루프
            login_success = False
            while True:
                try:
                    time.sleep(1)
                    
                    # 브라우저 창이 유효한지 먼저 확인 (사용자가 닫았는지 체크)
                    if not driver.window_handles:
                        self.after(0, lambda: self._log("ℹ️ 사용자에 의해 브라우저가 닫혔습니다."))
                        break
                        
                    curr_url = driver.current_url
                    cookies = driver.get_cookies()
                    
                    # 1. 특정 쿠키(NID_SES) 존재 확인
                    has_session_cookie = any(c['name'] == 'NID_SES' for c in cookies)
                    
                    # 2. URL이 이동했는지 확인
                    is_moved = "naver.com" in curr_url and ("nidlogin" not in curr_url)
                    
                    if has_session_cookie or (is_moved and "www.naver.com" in curr_url):
                        login_success = True
                        break
                except (WebDriverException, NoSuchWindowException):
                    # 사용자가 브라우저를 닫거나 연결이 끊긴 경우
                    self.after(0, lambda: self._log("ℹ️ 브라우저가 닫혀 로그인이 중단되었습니다."))
                    break
                except Exception as e:
                    # 기타 예상치 못한 에러
                    self.after(0, lambda: self._log(f"⚠️ 로그인 감지 중 오류: {str(e)}"))
                    break

            if login_success:
                # 메인 스레드에서 확인 팝업 표시
                self.after(0, lambda: self._confirm_and_apply_cookies(driver))
            else:
                self.after(0, lambda: self._log("ℹ️ 로그인이 완료되지 않은 채 브라우저가 닫혔습니다."))

        except Exception as e:
            self.after(0, lambda: self._log(f"❌ 셀레니움 오류: {str(e)}", error=True))
            if driver:
                driver.quit()

    def _confirm_and_apply_cookies(self, driver):
        """사용자 확인 후 쿠키 적용 및 브라우저 종료"""
        try:
            answer = messagebox.askyesno(
                "로그인 감지",
                "로그인이 감지되었습니다.\n이 세션을 다운로더에 적용하시겠습니까?",
                parent=self
            )
            
            if answer:
                selenium_cookies = driver.get_cookies()
                cookie_dict = {c['name']: c['value'] for c in selenium_cookies}
                
                success, msg = self.cookie_mgr.load_from_dict(cookie_dict, source="자동 로그인")
                self._update_cookie_status(success, msg)
                self._log(f"✅ 자동 로그인 쿠키 적용 완료 ({len(cookie_dict)}개)")
            
            driver.quit()
        except Exception as e:
            self._log(f"❌ 쿠키 적용 중 오류: {str(e)}", error=True)
            if driver:
                driver.quit()

    def _show_disclaimer(self):
        """프로그램 시작 시 면책 조항 팝업을 띄웁니다."""
        # 팝업 윈도우 설정
        dialog = tk.Toplevel(self)
        dialog.title("면책 조항 및 이용 안내")
        dialog.configure(bg=BG_COLOR)
        
        # 메인 윈도우의 자식 윈도우로 설정 및 포커스 고정 (모달)
        dialog.transient(self)
        dialog.grab_set()
        
        # 팝업 내용 프레임 (반응형 여백 설정)
        content_frame = tk.Frame(dialog, bg=SURFACE_COLOR, padx=30, pady=25)
        content_frame.pack(fill="both", expand=True, padx=20, pady=20)

        # 아이콘 또는 제목 레이블 (강조용 메가폰)
        tk.Label(
            content_frame,
            text="📢 안내 사항",
            font=FONT_TITLE,
            bg=SURFACE_COLOR,
            fg=ACCENT_COLOR
        ).pack(pady=(0, 15))

        # 면책 조항 본문 (사용자 요청 텍스트)
        disclaimer_text = (
            "웹툰을 받고 반드시 소장용으로만 사용해주세요. "
            "웹툰의 경우 엄연한 저작물이기에 무단배포시 법적 처벌을 받을 수 있습니다. "
            "본 프로그램은 프로그램 사용시 발생하는 법적 문제에 대해 일절 책임을 지지 않습니다. "
            "(면책 조항)"
        )
        
        tk.Label(
            content_frame,
            text=disclaimer_text,
            font=FONT_MAIN,
            bg=SURFACE_COLOR,
            fg=TEXT_COLOR,
            justify="center",
            wraplength=400  # 텍스트 너비에 따른 자동 줄바꿈 (반응형 느낌)
        ).pack(pady=(0, 20))

        # 확인 버튼
        tk.Button(
            content_frame,
            text="동의 및 확인",
            font=FONT_BOLD,
            bg=ACCENT_COLOR,
            fg="#fff",
            activebackground=ACCENT_HOVER,
            activeforeground="#fff",
            relief="flat",
            width=15,
            height=2,
            cursor="hand2",
            command=dialog.destroy
        ).pack()

        # 윈도우 크기 자동 조정 후 중앙 정렬 로직
        dialog.update_idletasks()
        
        # 중앙 위치 계산
        main_x = self.winfo_x()
        main_y = self.winfo_y()
        main_w = self.winfo_width()
        main_h = self.winfo_height()
        
        popup_w = dialog.winfo_width()
        popup_h = dialog.winfo_height()
        
        pos_x = main_x + (main_w // 2) - (popup_w // 2)
        pos_y = main_y + (main_h // 2) - (popup_h // 2)
        
        # 화면 밖으로 나가는 것 방지
        pos_x = max(0, pos_x)
        pos_y = max(0, pos_y)
        
        dialog.geometry(f"+{pos_x}+{pos_y}")
        
        # 팝업이 닫힐 때까지 대기 (모달 동작 보강)
        self.wait_window(dialog)

    # ───────────────────────────────────────────
    # 저장 경로
    # ───────────────────────────────────────────
    def _choose_save_path(self):
        """저장 경로 선택 다이얼로그"""
        path = filedialog.askdirectory(
            title="웹툰 저장 폴더 선택",
            initialdir=self.save_path,
            parent=self,
        )
        if path:
            self.save_path = path
            self.save_path_var.set(f"저장 경로: {path}")
            self._save_config()  # 변경된 경로를 설정 파일에 저장

    # ───────────────────────────────────────────
    # 웹툰 불러오기
    # ───────────────────────────────────────────
    def _load_webtoon(self):
        """URL 입력 → 웹툰 정보 및 회차 목록을 불러옵니다."""
        url = self.url_var.get().strip()
        if not url:
            messagebox.showwarning("입력 오류", "웹툰 URL을 입력해주세요.", parent=self)
            return

        title_id = extract_title_id(url, session=self.session)
        if not title_id:
            messagebox.showerror(
                "URL 오류",
                "올바른 웹툰 URL이 아닙니다.\n예: https://comic.naver.com/webtoon/list?titleId=12345\n(또는 naver.me 공유 링크)",
                parent=self,
            )
            return

        # UI 초기화
        self.current_title_id = title_id
        self.episode_listbox.delete(0, "end")
        self.all_episodes.clear()
        self._reset_info_panel()
        self.load_btn.config(state="disabled", text="불러오는 중...")
        self._log("웹툰 정보를 가져오는 중...")
        self._set_progress(0, "웹툰 정보 로딩 중...")

        threading.Thread(target=self._fetch_webtoon_data, args=(title_id,), daemon=True).start()

    def _fetch_webtoon_data(self, title_id: str):
        """백그라운드: 웹툰 정보 + 회차 목록 수집"""
        try:
            # 1. 웹툰 기본 정보
            info = get_webtoon_info(self.session, title_id)
            self.current_webtoon_info = info
            self.after(0, lambda: self._update_info_panel(info))

            # 2. 회차 목록 (페이지 단위로 진행률 업데이트)
            def on_page_progress(cur, total):
                pct = (cur / max(total, 1)) * 80  # 80%까지 회차 목록 로딩
                self.after(0, lambda: self._set_progress(pct, f"회차 목록 로딩 중... ({cur}/{total} 페이지)"))

            episodes = get_all_episodes(self.session, title_id, on_page_progress)
            self.all_episodes = episodes

            self.after(0, lambda: self._populate_episode_list(episodes))
            self.after(0, lambda: self._set_progress(100, f"총 {len(episodes)}화 로딩 완료"))
        except RatingError as e:
            def ask_login():
                if messagebox.askyesno("성인 인증 필요", f"{e}\n\n지금 [자동 로그인]을 진행하시겠습니까?", parent=self):
                    self._auto_login()
            self.after(0, ask_login)
            self.after(0, lambda: self._on_load_error(str(e), show_dialog=False))
        except WebtoonNotFoundError as e:
            self.after(0, lambda: self._on_load_error(str(e)))
        except WebtoonError as e:
            self.after(0, lambda: self._on_load_error(str(e)))
        except Exception as e:
            self.after(0, lambda: self._on_load_error(str(e)))
        finally:
            self.after(0, lambda: self.load_btn.config(state="normal", text="🔍 불러오기"))

    def _on_load_error(self, msg: str, show_dialog: bool = True):
        """웹툰 로딩 오류 처리"""
        display_msg = msg if msg and msg != "None" else "알 수 없는 에러가 발생했습니다. (쿠키 확인 필요)"
        self._log(f"❌ 오류: {display_msg}", error=True)
        self._set_progress(0, "로딩 실패")
        if show_dialog:
            messagebox.showerror("로딩 오류", display_msg, parent=self)

    def _reset_info_panel(self):
        """웹툰 정보 패널을 초기 상태로 되돌립니다."""
        self.webtoon_title_var.set("불러오는 중...")
        self.author_var.set("")
        self.genre_var.set("")
        self.synopsis_var.set("")
        self.thumb_label.config(image="", text="🖼", font=("Segoe UI", 32))
        self.thumbnail_photo = None

    def _update_info_panel(self, info: dict):
        """웹툰 정보를 UI에 표시합니다."""
        status = "완결" if info.get("finish") else "연재 중"
        total = info.get("totalEpisodeCount", "?")
        webtoon_type_kr = {
            "webtoon": "웹툰",
            "bestChallenge": "베스트도전",
            "challenge": "도전만화"
        }.get(info.get("webtoon_type", "webtoon"), "웹툰")

        self.webtoon_title_var.set(f"{info.get('titleName', '제목 없음')}  [{webtoon_type_kr} / {status}]")
        self.author_var.set(f"✍ 작가: {info.get('author', '알 수 없음')}")
        self.genre_var.set(f"🏷 장르: {info.get('genre', '미분류')}  |  📖 총 {total}화")
        synopsis = info.get("synopsis", "") or ""
        if len(synopsis) > 120:
            synopsis = synopsis[:120] + "..."
        self.synopsis_var.set(f"📝 {synopsis}" if synopsis else "")

        # 썸네일 비동기 로드
        thumb_url = info.get("thumbnail", "")
        if thumb_url:
            threading.Thread(
                target=self._load_thumbnail, args=(thumb_url,), daemon=True
            ).start()

        self._log(f"✅ [{webtoon_type_kr}] '{info.get('titleName')}' 정보 로딩 완료")

    def _load_thumbnail(self, url: str):
        """썸네일 이미지를 백그라운드로 다운받아 GUI에 표시합니다."""
        try:
            resp = self.session.get(
                url,
                headers={"Referer": "https://comic.naver.com/"},
                timeout=15,
            )
            resp.raise_for_status()
            img = Image.open(BytesIO(resp.content))
            img.thumbnail((120, 160), Image.LANCZOS)
            photo = ImageTk.PhotoImage(img)
            self.after(0, lambda: self._set_thumbnail(photo))
        except Exception:
            pass

    def _set_thumbnail(self, photo: ImageTk.PhotoImage):
        """썸네일을 GUI에 적용합니다. (메인 스레드에서 호출)"""
        self.thumbnail_photo = photo
        self.thumb_label.config(image=photo, text="")

    # ───────────────────────────────────────────
    # 회차 목록
    # ───────────────────────────────────────────
    def _populate_episode_list(self, episodes: list):
        """회차 목록 리스트박스를 채웁니다."""
        self.episode_listbox.delete(0, "end")

        # sort_desc_var 에 따라 순서 결정
        display_eps = episodes if not self.sort_desc_var.get() else list(reversed(episodes))

        for ep in display_eps:
            charged_tag = "  [🔒유료]" if ep.get("is_charged") else ""
            label = f"  {ep['no']:>4}화  {ep['title']:<38}{charged_tag}  {ep['date']}"
            self.episode_listbox.insert("end", label)

        self.ep_count_var.set(f"회차 목록  (총 {len(episodes)}화)")

        # 상단 정보 패널의 총 회차 수 다시 업데이트
        if self.current_webtoon_info:
            genre = self.current_webtoon_info.get("genre", "미분류")
            self.genre_var.set(f"🏷 장르: {genre}  |  📖 총 {len(episodes)}화")

        self._log(f"📋 총 {len(episodes)}화 목록 표시 완료")

    def _sort_episodes(self):
        """정렬 순서 변경 시 목록을 다시 표시합니다."""
        if self.all_episodes:
            self._populate_episode_list(self.all_episodes)

    def _select_all(self):
        """전체 회차 선택"""
        self.episode_listbox.select_set(0, "end")

    def _deselect_all(self):
        """전체 회차 선택 해제"""
        self.episode_listbox.select_clear(0, "end")

    def _get_selected_episodes(self) -> list[dict]:
        """현재 선택된 회차 목록을 반환합니다."""
        selected_indices = self.episode_listbox.curselection()
        if not selected_indices:
            return []

        # 리스트박스 표시 순서와 실제 에피소드 순서를 맞춤
        display_eps = (
            self.all_episodes
            if not self.sort_desc_var.get()
            else list(reversed(self.all_episodes))
        )

        return [display_eps[i] for i in selected_indices if i < len(display_eps)]

    def _add_to_queue(self):
        """현재 선택된 회차들을 대기열에 추가합니다."""
        if not self.current_title_id:
            messagebox.showwarning("입력 오류", "먼저 웹툰을 불러와주세요.", parent=self)
            return

        selected = self._get_selected_episodes()
        if not selected:
            messagebox.showwarning("선택 없음", "대기열에 추가할 회차를 선택해주세요.", parent=self)
            return

        # 대기열에 추가 (정보, 선택된 회차, 저장 경로)
        task = {
            "title_id": self.current_title_id,
            "title_name": self.current_webtoon_info.get("titleName", "Unknown"),
            "thumbnail": self.current_webtoon_info.get("thumbnail", ""),
            "webtoon_type": self.current_webtoon_info.get("webtoon_type", "webtoon"),
            "episodes": selected,
            "save_path": self.save_path
        }
        with self._lock:
            self.download_queue.append(task)
        self._update_queue_listbox()
        self._update_queue_tab_title()
        
        # 안내 메시지 및 탭 이동 시각화 (선택 사항)
        self._log(f"➕ '{task['title_name']}' {len(selected)}개 회차를 대기열에 추가했습니다.")
        # messagebox.showinfo("성공", f"'{task['title_name']}' {len(selected)}개 회차가 대기열에 추가되었습니다.", parent=self)

    def _update_queue_tab_title(self):
        """대기열 탭 버튼에 실시간 작업 개수 뱃지를 업데이트합니다."""
        count = len(self.download_queue)
        text = f"📋  대기열 관리 ({count})" if count > 0 else "📋  대기열 관리"
        try:
            self.btn_queue_tab.config(text=text)
        except Exception:
            pass

    def _update_queue_listbox(self):
        """대기열 리스트박스를 최신화합니다."""
        self.queue_listbox.delete(0, "end")
        for i, task in enumerate(self.download_queue, 1):
            label = f"  {i}. {task['title_name']} ({len(task['episodes'])}화)  -  준비 완료"
            self.queue_listbox.insert("end", label)
        self._update_queue_tab_title()

    def _remove_from_queue(self):
        """대기열에서 선택된 항목을 삭제합니다."""
        idx = self.queue_listbox.curselection()
        if not idx:
            return
        
        # 역순으로 삭제하여 인덱스 꼬임 방지
        with self._lock:
            for i in reversed(idx):
                task = self.download_queue.pop(i)
                self._log(f"➖ 대기열에서 '{task['title_name']}' 제거됨")
        
        self._update_queue_listbox()

    # ───────────────────────────────────────────
    # 다운로드
    # ───────────────────────────────────────────
    def _start_download(self):
        """선택된 회차 즉시 다운로드 시작"""
        if self.is_downloading:
            messagebox.showinfo("다운로드 중", "이미 다운로드가 진행 중입니다.", parent=self)
            return

        if not self.current_title_id:
            messagebox.showwarning("웹툰 없음", "먼저 웹툰을 불러와주세요.", parent=self)
            return

        selected = self._get_selected_episodes()
        if not selected:
            messagebox.showwarning("선택 없음", "다운로드할 회차를 선택해주세요.", parent=self)
            return

        # 확인 다이얼로그
        title_name = self.current_webtoon_info.get("titleName", "") if self.current_webtoon_info else ""
        answer = messagebox.askyesno(
            "다운로드 확인",
            f"'{title_name}'\n선택한 {len(selected)}개 회차를 즉시 다운로드합니다.\n\n계속하시겠습니까?",
            parent=self,
        )
        if not answer:
            return

        task = {
            "title_id": self.current_title_id,
            "title_name": title_name,
            "thumbnail": self.current_webtoon_info.get("thumbnail", "") if self.current_webtoon_info else "",
            "webtoon_type": self.current_webtoon_info.get("webtoon_type", "webtoon") if self.current_webtoon_info else "webtoon",
            "episodes": selected,
            "save_path": self.save_path
        }

        with self._lock:
            self.is_downloading = True
            self._set_ui_state("disabled")
        threading.Thread(target=self._download_worker, args=([task],), daemon=True).start()

    def _start_queue_download(self):
        """대기열에 담긴 모든 웹툰 다운로드 시작"""
        if self.is_downloading:
            messagebox.showinfo("다운로드 중", "이미 다운로드가 진행 중입니다.", parent=self)
            return

        if not self.download_queue:
            messagebox.showwarning("대기열 비었음", "대기열에 작업이 없습니다.", parent=self)
            return

        answer = messagebox.askyesno(
            "일괄 다운로드",
            f"대기열에 있는 {len(self.download_queue)}개의 웹툰을 모두 다운로드하시겠습니까?",
            parent=self
        )
        if not answer:
            return

        # 원자적으로 대기열 복사 및 비우기, 상태 변경
        with self._lock:
            tasks = list(self.download_queue)
            self.download_queue.clear()
            self.is_downloading = True
            self._set_ui_state("disabled")
        
        self._update_queue_listbox()
        threading.Thread(target=self._download_worker, args=(tasks,), daemon=True).start()

    def _set_ui_state(self, state: str):
        """다운로드 중/종료 시 버튼 상태를 일괄 변경합니다."""
        self.download_btn.config(state=state)
        self.add_queue_btn.config(state=state)
        self.start_queue_btn.config(state=state)
        self.load_btn.config(state=state)

    def _download_worker(self, tasks: list[dict]):
        """백그라운드: 대기열에 있는 작업들을 순차적으로 처리"""
        try:
            with concurrent.futures.ThreadPoolExecutor(max_workers=16) as down_executor:
                total_tasks = len(tasks)
                for t_idx, task in enumerate(tasks, 1):
                    title_id = task["title_id"]
                    webtoon_name = task["title_name"]
                    webtoon_type = task.get("webtoon_type", "webtoon")
                    episodes = task["episodes"]
                    save_path = task["save_path"]
                    total_eps = len(episodes)

                    self.after(0, lambda n=webtoon_name, i=t_idx, tot=total_tasks: 
                               self._log(f"\n📂 [{i}/{tot}] '{n}' 작업 시작..."))

                    # ── 1. 웹툰 폴더 생성 및 포스터 저장 ──
                    webtoon_folder = make_webtoon_folder(save_path, webtoon_name)
                    
                    # 대표 포스터(썸네일) 저장
                    thumbnail_url = task.get("thumbnail")
                    if thumbnail_url:
                        ext = thumbnail_url.split(".")[-1].split("?")[0]
                        if ext.lower() not in ("jpg", "jpeg", "png", "webp", "gif"):
                            ext = "jpg"
                        poster_path = os.path.join(webtoon_folder, f"{sanitize_filename(webtoon_name)}.{ext}")
                        
                        if not os.path.exists(poster_path):
                            download_thumbnail(self.session, thumbnail_url, poster_path)

                    # ── 2. 각 회차 다운로드 ──
                    for idx, ep in enumerate(episodes, 1):
                        ep_no = ep["no"]
                        ep_title = ep["title"]
                        is_charged = ep.get("is_charged", False)

                        self.after(0, lambda i=idx, t=total_eps, et=ep_title, ti=t_idx: 
                                   self._set_progress((i - 1) / t * 100, f"[{ti}/{total_tasks}] {et} 준비 중..."))
                        
                        try:
                            # 회차 데이터 가져오기 (이미지 목록, BGM 오디오 URL, 작가의 말)
                            ep_data = get_episode_data(self.session, title_id, ep_no, webtoon_type=webtoon_type)
                            image_urls = ep_data.get("images", [])
                            audio_url = ep_data.get("audio")
                            author_words = ep_data.get("author_words", "")

                            ep_folder = make_episode_folder(save_path, webtoon_name, ep_no, ep_title)

                            # 작가의 말 메타데이터 저장 (info.json)
                            if author_words:
                                info_path = os.path.join(ep_folder, "info.json")
                                try:
                                    with open(info_path, "w", encoding="utf-8") as f:
                                        json.dump({"author_words": author_words}, f, ensure_ascii=False, indent=2)
                                except Exception:
                                    pass

                            # 베스트 댓글 수집 및 저장 (comments.json)
                            try:
                                comments = get_episode_comments(self.session, title_id, ep_no, limit=15)
                                if comments:
                                    comments_path = os.path.join(ep_folder, "comments.json")
                                    with open(comments_path, "w", encoding="utf-8") as f:
                                        json.dump(comments, f, ensure_ascii=False, indent=2)
                            except Exception:
                                pass

                            # BGM 다운로드 (있을 경우 bgm.mp3 저장)
                            if audio_url:
                                audio_path = os.path.join(ep_folder, "bgm.mp3")
                                if not os.path.exists(audio_path):
                                    download_audio(self.session, audio_url, audio_path)

                            img_total = len(image_urls)
                            success_count = [0]
                            completed = [0]

                            def download_single(img_idx, img_url):
                                ext = img_url.split(".")[-1].split("?")[0]
                                if ext.lower() not in ("jpg", "jpeg", "png", "webp", "gif"):
                                    ext = "jpg"
                                img_path = os.path.join(ep_folder, f"{img_idx:03d}.{ext}")

                                if os.path.exists(img_path) and os.path.getsize(img_path) > 0:
                                    return True
                                return download_image(self.session, img_url, img_path, title_id)

                            # 이미지 다운로드 (공용 down_executor 사용)
                            future_to_url = {down_executor.submit(download_single, i, url): i for i, url in enumerate(image_urls, 1)}
                            for future in concurrent.futures.as_completed(future_to_url):
                                if future.result(): success_count[0] += 1
                                completed[0] += 1
                                ep_pct = ((idx - 1) + completed[0] / max(img_total, 1)) / total_eps * 100
                                self.after(0, lambda p=ep_pct, i=idx, mi=completed[0], mt=img_total, t=ep_title, ti=t_idx: 
                                           self._set_progress(p, f"[{ti}/{total_tasks}] {t} ({mi}/{mt})"))

                            bgm_tag = " [🎵BGM]" if audio_url else ""
                            self.after(0, lambda n=webtoon_name, e=ep_no, t=ep_title, s=success_count[0], m=img_total, b=bgm_tag: 
                                       self._log(f"  └ {n} - {e}화 - {t}{b} - 완료 ({s}/{m}장)"))

                        except Exception as e:
                            err_msg = str(e)
                            if is_charged:
                                self.after(0, lambda n=ep_no, t=ep_title: 
                                           self._log(f"  └ 🔒 {n}화 ({t}) - 유료/미리보기 회차이므로 건너뜁니다."))
                            else:
                                self.after(0, lambda n=ep_no, err=err_msg: 
                                           self._log(f"  └ ❌ {n}화 오류: {err}", error=True))

                    # ── 3. 한 웹툰 작업 완료 후 HTML 뷰어 생성 ──
                    try:
                        self.after(0, lambda n=webtoon_name: self._log(f"  📦 '{n}' 모아보기 생성 중..."))
                        generate_viewer(webtoon_folder)
                    except Exception as e:
                        self.after(0, lambda err=str(e): self._log(f"  ❌ 뷰어 생성 오류: {err}", error=True))

            self.after(0, lambda: self._set_progress(100, "✅ 모든 작업 완료!"))
            self.after(0, lambda: self._log(f"\n🎉 대기열의 모든 다운로드가 완료되었습니다."))
            self.after(0, lambda: messagebox.showinfo("완료", "모든 다운로드가 완료되었습니다!", parent=self))

        except Exception as e:
            self.after(0, lambda err=str(e): self._log(f"❌ 치명적 오류: {err}", error=True))
        finally:
            self.is_downloading = False
            self.after(0, lambda: self._set_ui_state("normal"))

    # ───────────────────────────────────────────
    # 버전 체크
    # ───────────────────────────────────────────
    def _check_version(self):
        """서버에서 최신 버전을 확인합니다."""
        try:
            # 타임아웃을 짧게 설정하여 시작 시 지연 최소화
            resp = requests.get(VERSION_CHECK_URL, timeout=5)
            if resp.status_code == 200:
                data = resp.json()
                latest_version = data.get("latest_version", APP_VERSION)
                
                # 시맨틱 버저닝 비교 (간단히 문자열 비교 또는 점 구분 비교 가능)
                if latest_version > APP_VERSION:
                    def ask_update():
                        ans = messagebox.askyesno(
                            "새로운 버전 발견",
                            f"새로운 업데이트(v{latest_version})가 있습니다.\n"
                            "지금 다운로드 페이지로 이동하시겠습니까?",
                            parent=self
                        )
                        if ans:
                            webbrowser.open(DOWNLOAD_URL)
                    
                    self.after(0, ask_update)
        except Exception:
            pass # 네트워크 오류 등은 조용히 무음 처리

    # ───────────────────────────────────────────
    # 공통 유틸
    # ───────────────────────────────────────────
    def _set_progress(self, value: float, label: str = ""):
        """진행률 바와 레이블을 업데이트합니다. (메인 스레드에서만 호출)"""
        self.progress_var.set(min(value, 100))
        if label:
            self.progress_label_var.set(label)

    def _log(self, message: str, error: bool = False):
        """로그 텍스트 영역에 메시지를 추가합니다. (메인 스레드에서만 호출)"""
        self.log_text.config(state="normal")
        tag = "error" if error else "normal"
        self.log_text.insert("end", f"{message}\n", tag)
        self.log_text.see("end")   # 자동 스크롤
        self.log_text.config(state="disabled")


# ─────────────────────────────────────────────
# 진입점
# ─────────────────────────────────────────────
if __name__ == "__main__":
    app = WebtoonDownloader()
    app.mainloop()
