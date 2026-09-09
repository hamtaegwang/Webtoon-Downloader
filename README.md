# Webtoon Downloader & Offline Viewer

<p align="center">
  <strong>A desktop GUI utility to download webtoon episodes and generate responsive offline HTML viewers.</strong><br>
  웹툰 회차를 저장하고 오프라인에서 읽을 수 있는 고품질 반응형 HTML 뷰어를 생성하는 데스크톱 프로그램입니다.
</p>

<p align="center">
  <img src="https://img.shields.io/badge/Python-3.12%2B-blue?logo=python" alt="Python Version">
  <img src="https://img.shields.io/badge/GUI-Tkinter-green" alt="Tkinter">
  <img src="https://img.shields.io/badge/License-MIT-yellow.svg" alt="License: MIT">
  <img src="https://img.shields.io/badge/Platform-Windows-lightgrey?logo=windows" alt="Platform: Windows">
</p>

---

## 📖 English Overview

**Webtoon Downloader** is an open-source Windows desktop application built with Python and Tkinter. It allows users to archive webtoon episodes locally and generates an interactive, mobile-responsive offline HTML viewer equipped with dark mode, smooth scrolling, and episode navigation.

### Key Features
- **Responsive HTML Viewer Generation**: Automatically creates full-featured offline viewers (`[Title] 미리보기.html` and episode-specific `index.html`) supporting dark theme, dropdown episode switching, and keyboard navigation.
- **Multi-Strategy Image Extraction**: Resilient scraping engine using structured JSON parsing (`__NEXT_DATA__`, `window.__state__`), DOM selectors, and regex fallbacks.
- **Multithreaded Performance**: Parallel image sequence verification and downloading using `ThreadPoolExecutor` for maximum responsiveness without freezing the GUI.
- **Session Authentication Manager**: Supports browser cookie session injection for user-authorized content access.
- **Native Windows Desktop Experience**: Fully optimized for Windows High-DPI displays with taskbar integration and custom multi-resolution icons.

---

## 🇰🇷 한국어 소개

**Webtoon Downloader**는 웹툰을 로컬 환경에 보관하고, 인터넷 연결이 없거나 불안정한 환경에서도 실제 웹툰 플랫폼과 동일한 경험으로 감상할 수 있도록 독립형 HTML 뷰어를 자동 생성해 주는 오픈소스 데스크톱 유틸리티입니다.

### 주요 기능
- **오프라인 반응형 HTML 뷰어 자동 생성**: 다크 모드, 상/하단 빠른 네비게이션, 회차 이동 드롭다운, 스크롤 반응형 UI가 내장된 단독 뷰어 생성.
- **안정적인 4단계 이미지 추출 엔진**: 웹사이트 구조 변경에 유연하게 대응하는 다단계 파싱 전략.
- **UI 프리징 없는 멀티스레딩**: 다운로드 중에도 매끄러운 GUI 조작 지원.
- **공인 디지털 서명 지원**: SignPath Foundation 무료 공인 코드 서명을 통해 Windows 11 Smart App Control(SAC) 및 Defender SmartScreen 경고 없는 안전한 단일 실행 파일(.exe) 배포.

---

## 📦 다운로드 (Download)

Windows 사용자라면 별도의 Python 설치나 복잡한 압축 해제 없이 **단 하나의 공인 서명 실행 파일**만 다운로드하여 즉시 사용할 수 있습니다.

- 👉 **[최신 릴리즈 다운로드 (GitHub Releases)](https://github.com/hamtaegwang/Webtoon-Downloader/releases)**
  - 다운로드 파일: `Webtoon Downloader v{version}.exe` (공인 서명 완료된 단일 파일)

> [!NOTE]
> 코드 서명 파이프라인 구성 및 SignPath 연동 가이드는 [`docs/SIGNPATH_SETUP_GUIDE.md`](docs/SIGNPATH_SETUP_GUIDE.md)를 참고하세요.

---

## 🚀 개발 및 직접 빌드 (Getting Started)

### 1. 소스 코드에서 실행
```bash
# 저장소 클론
git clone https://github.com/hamtaegwang/Webtoon-Downloader.git
cd Webtoon-Downloader

# 의존성 패키지 설치
pip install -r requirements.txt

# 프로그램 실행
python src/main.py
```

### 2. 단일 실행 파일(.exe) 빌드
```bash
# 원클릭 빌드 스크립트 실행
build.bat
```
빌드가 완료되면 `dist/` 폴더에 `Webtoon Downloader v{version}.exe` 단일 실행 파일이 생성됩니다.

---

## 🛡️ 면책 조항 (Disclaimer)

본 프로그램은 개인적인 연구, 학습 및 오프라인 보관 목적을 위해 비영리 오픈소스로 개발되었습니다. 저작권이 있는 모든 콘텐츠의 권리는 원저작자 및 서비스 제공자에게 있습니다. 본 소프트웨어의 사용으로 인해 발생하는 모든 법적 책임은 사용자 본인에게 있습니다.

---

## 📄 라이선스 (License)

This project is licensed under the terms of the [MIT License](LICENSE).
