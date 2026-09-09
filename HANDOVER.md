# Webtoon Downloader - Handover Document

이 문서는 프로젝트를 다음 개발자(또는 Claude 등 AI 어시스턴트)가 이어받을 수 있도록 핵심 정보와 현재 상태를 요약한 가이드입니다.

## 🚀 프로젝트 개요 (Overview)
- **목적**: 웹툰을 회차별로 다운로드하고, 오프라인에서도 웹툰처럼 볼 수 있는 HTML 뷰어를 생성하는 도구.
- **언어 및 프레임워크**: Python 3.12+, Tkinter (GUI), Requests & BeautifulSoup (Scraping), PyInstaller (Packaging).

## 🏗 핵심 아키텍처 (Core Architecture)

### 1. `src/main.py` (Main GUI)
- Tkinter 기반의 메인 UI.
- 모든 네트워크 요청 및 파일 입출력은 UI 프리징을 방지하기 위해 `threading`을 통한 백그라운드 작업으로 처리.
- 윈도우 High DPI 인식 설정 및 AppUserModelID 설정을 포함하여 작업표시줄 아이콘 대응 완료.

### 2. `src/webtoon_api.py` (Core Logic)
- **추출 전략**: 웹툰 사이트의 최신 변경 사항에 대응하기 위해 4단계 전략 사용.
    - JSON 파싱 (`__NEXT_DATA__`, `window.__state__`)
    - DOM 셀렉터 분석
    - Regex 패턴 분석
    - 모바일 페이지 폴백 (마지막 수단)
- **병렬 처리**: `_recover_sequence` 함수에서 `ThreadPoolExecutor`를 사용하여 이미지 시퀀스를 빠르게 검증(HEAD 요청)하고 수집.

### 3. `src/html_generator.py` (Offline Viewer)
- 다운로드 완료 후 다크 모드 테마의 HTML 뷰어 생성.
- 웹툰 루트에 `[제목] 미리보기.html` (메인 목록) 생성.
- 각 회차 폴더 내 `index.html` (개별 뷰어) 생성.
- 상단/하단 네비게이션, 회차 이동 드롭다운, 스크롤 반응형 UI 포함.

### 4. `src/cookie_manager.py` (Authentication)
- 유료/로그인 제한 회차를 위한 쿠키 관리 로직.
- 브라우저 개발자 도구의 Raw Cookie 문자열을 복사-붙여넣기하여 세션을 활성화할 수 있는 기능 제공.

## 🛠 빌드 및 배포 (Build & Release Guide)

### 1. [공식 정식 배포] SignPath Foundation 무료 공인 서명 단일 .exe (CI/CD)
- **파이프라인**: `.github/workflows/release.yml`
- **배포 방식**: GitHub Actions에서 PyInstaller로 단일 `.exe`를 빌드한 후, SignPath Foundation을 통해 공인 Authenticode 디지털 서명을 받아 GitHub Releases에 **단일 `.exe` 단독으로 자동 배포**.
- **장점**:
  - Windows 11 Smart App Control (SAC) 차단 100% 원천 해결.
  - Microsoft Defender 및 SmartScreen의 "알 수 없는 게시자" 경고 해결.
  - 압축 해제나 복잡한 폴더 구조 없이 단 1개의 파일만 다운로드하여 즉시 실행 가능.
- **설정 가이드**: 상세 설정 및 신청 방법은 [`docs/SIGNPATH_SETUP_GUIDE.md`](docs/SIGNPATH_SETUP_GUIDE.md) 참조.

### 2. [로컬 개발용] PyInstaller 로컬 단일 실행 파일
- **빌드 스크립트**: `build.bat`
- **방식**: PyInstaller의 `.spec` 기반 로컬 단일 실행 파일 빌드 (`upx=False`, `version info` 리소스 적용).
- **결과물**: `dist/Webtoon Downloader v{version}.exe` 생성.

### 3. [대체 수단] 무설치 포터블 패키지
- **빌드 스크립트**: `build_portable.bat` (또는 `python build_portable.py`)
- **특징**: Python Software Foundation(PSF) 정품 서명 런처 기반의 디렉토리 압축 배포판.

## ✅ 최근 작업 내역 (Recent Updates)
1. **코드 정리**: 프로젝트 루트에 산재해 있던 중복 `.spec` 파일 5개와 레거시 배치 파일들을 삭제하고 `Webtoon Downloader.spec`으로 통합함.
2. **리팩토링**: `utils.py`로 공통 기능을 분리하고, 이미지 추출 로직의 안정성을 대폭 개선함.
3. **경로 문제 해결**: 실행 파일(Frozen 환경)과 소스 코드 실행 환경 모두에서 리소스를 찾을 수 있도록 `get_resource_path` 유틸리티 적용.
4. **SignPath Foundation 공인 코드 서명 파이프라인 구축**: `.github/workflows/release.yml`에 최신 SignPath 제출/검증/단일 exe 릴리즈 액션 구축 및 온보딩 가이드(`docs/SIGNPATH_SETUP_GUIDE.md`) 작성 완료.
5. **버전 리소스 주입 자동화**: `generate_version_info.py`에서 환경 변수 `VERSION` 우선 감지 및 PE 버전 정보 자동 생성 지원.


## 📌 다음 단계 및 개선 제안
- **안정성**: 회차별 다운로드 실패 시 재시도 로직 강화.
- **UX**: 다운로드 속도 제한 설정을 추가하여 사이트 측의 차단 우려 감소.
- **기능**: 여러 편의 웹툰을 대기열에 담아 일괄 다운로드하는 기능.

---
이 프로젝트를 Claude에서 이어가실 경우, `src/` 폴더 내의 각 파일을 읽어 현재 구현된 멀티 스텝 추출 로직을 먼저 파악하는 것을 권장합니다.
