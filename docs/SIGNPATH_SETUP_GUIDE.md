# SignPath Foundation 무료 공인 서명 설정 가이드 (A to Z)

이 문서는 **Webtoon Downloader**의 단일 실행 파일(`.exe`)에 **SignPath Foundation**의 무료 공인 코드 서명(Authenticode Signature)을 적용하기 위해 필요한 모든 외부 설정 과정을 안내합니다.

설정을 완료하면 Windows 11의 **Smart App Control (SAC)** 차단 및 **Microsoft Defender SmartScreen** '알 수 없는 게시자' 경고가 완전히 해결된 정품 소프트웨어 인증 실행 파일이 자동으로 빌드 및 배포됩니다.

---

## 📋 사전 준비 사항 (체크리스트)
- [x] 오픈소스 라이선스: `LICENSE` (MIT License 완료)
- [x] 공개 GitHub 저장소: `hamtaegwang/Webtoon-Downloader`
- [x] CI/CD 워크플로우 구성: `.github/workflows/release.yml` 준비 완료
- [x] PE 버전 정보 및 아이콘 최적화: `file_version_info.txt`, `icon.ico`, `upx=False` 적용 완료

---

## 🚀 1단계: SignPath Foundation 무료 오픈소스 서명 신청

SignPath Foundation은 비영리 및 오픈소스 프로젝트에 무료로 공인 코드 서명 인증서를 지원합니다.

1. **신청 페이지 접속**:
   👉 [https://signpath.org/apply.html](https://signpath.org/apply.html)
2. **신청 양식 작성 요령**:
   - **Project Name**: `Webtoon Downloader`
   - **Project Repository**: `https://github.com/hamtaegwang/Webtoon-Downloader`
   - **License**: `MIT License` (OSI 승인 라이선스)
   - **Project Description**:
     > Webtoon Downloader is a free, open-source desktop utility for downloading webtoons for offline viewing with an interactive responsive HTML viewer.
   - **Intended Artifact to Sign**: `Windows Executable (.exe)`
   - **Build System**: `GitHub Actions`
   - **Email & Name**: 관리자 본인 정보 입력
3. **신청서 제출 및 심사**:
   - 제출 후 SignPath 팀의 오픈소스 검토(통상 영업일 기준 1~3일)가 진행됩니다.
   - 승인 메일이 도착하면 계정 활성화 링크를 통해 비밀번호를 설정하고 로그인합니다.

---

## ⚙️ 2단계: SignPath 대시보드 프로젝트 설정

SignPath에 로그인한 후 조직(Organization)과 프로젝트(Project)를 설정합니다.

1. **조직 ID (Organization ID) 확인**:
   - 좌측 메뉴 상단 또는 Organization Settings에서 조직의 고유 ID(UUID 형태, 예: `a1b2c3d4-e5f6-...`)를 복사해 둡니다.
2. **프로젝트(Project) 생성**:
   - `Projects` -> `Add project` 클릭
   - **Project Name**: `Webtoon Downloader`
   - **Project Slug**: `webtoon-downloader` (소문자, 하이픈 권장)
3. **서명 정책(Signing Policy) 생성**:
   SignPath에서는 일반적으로 두 가지 서명 정책을 사용합니다:
   - **Release Signing Policy**:
     - Name: `Release Signing`
     - Slug: `release-signing`
     - 용도: `v*` 태그 푸시 시 공식 공인 서명 적용
   - **Test Signing Policy**:
     - Name: `Test Signing`
     - Slug: `test-signing`
     - 용도: `workflow_dispatch` 수동 실행 시 파이프라인 검증용
4. **API Token 발급**:
   - `API Tokens` 또는 `Service Accounts` 메뉴로 이동
   - 새 토큰 생성 (설명: `GitHub Actions CI Token`)
   - 생성된 API Token 값을 안전하게 복사해 둡니다. (한 번만 표시됨)

---

## 🔗 3단계: GitHub에 SignPath GitHub App 설치

SignPath의 보안 원칙(Origin Verification: 신뢰할 수 있는 GitHub 빌드 러너에서만 서명 허용)을 위해 저장소에 공식 GitHub App을 설치해야 합니다.

1. **SignPath GitHub App 설치 페이지**:
   👉 [https://github.com/apps/signpath](https://github.com/apps/signpath)
2. **저장소 선택**:
   - `Only select repositories` 선택 후 `Webtoon-Downloader` 리포지토리 지정
   - `Install & Authorize` 클릭 완료

---

## 🔐 4단계: GitHub Repository Secrets 및 Variables 등록

GitHub 리포지토리의 `Settings` -> `Secrets and variables` -> `Actions` 메뉴에서 아래 항목들을 등록합니다.

### 1) Repository Secrets (비밀 값)
| 이름 | 설명 | 값 예시 |
| :--- | :--- | :--- |
| `SIGNPATH_API_TOKEN` | 2단계에서 발급받은 API 토큰 | `sp_tok_...` |

### 2) Repository Variables (환경 변수)
| 이름 | 설명 | 값 예시 |
| :--- | :--- | :--- |
| `SIGNPATH_ORGANIZATION_ID` | SignPath 조직 고유 ID (UUID) | `12345678-abcd-...` |
| `SIGNPATH_PROJECT_SLUG` | 프로젝트 슬러그 명칭 | `webtoon-downloader` |
| `SIGNPATH_SIGNING_POLICY_SLUG` | 정식 릴리즈용 서명 정책 슬러그 | `release-signing` |
| `SIGNPATH_TEST_SIGNING_POLICY_SLUG` | 수동 테스트용 서명 정책 슬러그 | `test-signing` |

*(참고: `SIGNPATH_PROJECT_SLUG`나 정책 슬러그는 설정하지 않더라도 기본값으로 각각 `webtoon-downloader`, `release-signing`, `test-signing`이 자동 적용되도록 워크플로우에 안전장치가 되어 있습니다.)*

---

## 🧪 5단계: 파이프라인 테스트 및 정식 배포

### 1) 파이프라인 사전 테스트 (Test Signing)
1. GitHub 리포지토리의 `Actions` 탭으로 이동합니다.
2. 좌측 워크플로우 목록에서 `Build, Sign and Release`를 클릭합니다.
3. 우측의 `Run workflow` 버튼을 누르고 브랜치(`main`)를 선택한 뒤 실행합니다.
4. 워크플로우가 실행되면서:
   - Python 환경 설정 및 단일 `.exe` 빌드
   - SignPath에 테스트 서명 요청 제출
   - 서명 완료 대기 및 다운로드
   - `Get-AuthenticodeSignature` 유효성 검증
   - 실행 결과(Artifacts)에 `Webtoon_Downloader_v{version}_Signed_EXE` 업로드
5. 아티팩트를 다운로드하여 실행 속성에서 서명 탭이 생성되었는지 확인합니다.

### 2) 정식 릴리즈 배포 (Release Signing)
새로운 버전을 배포할 때는 Git 태그를 생성하고 푸시하기만 하면 됩니다.

```bash
# 1. 최신 커밋 확인 후 버전 태그 생성 (예: v1.0.5)
git tag v1.0.5

# 2. 원격 저장소로 태그 푸시
git push origin v1.0.5
```

- GitHub Actions가 태그 푸시를 감지하여 자동으로 `release-signing` 정책으로 공인 서명을 수행합니다.
- 서명 검증 통과 후 **GitHub Releases**에 오직 공인 서명된 단일 파일인 **`Webtoon Downloader v1.0.5.exe`**만 깔끔하게 등록 및 배포됩니다!

---

## 🛡️ 최종 서명 결과 확인 방법 (Windows)

생성된 실행 파일 우클릭 -> **속성(Properties)** -> **디지털 서명(Digital Signatures)** 탭에서:
- **서명자 이름**: `SignPath Foundation`
- **다이제스트 알고리즘**: `sha256`
- **타임스탬프**: 공인 타임스탬프 서버 기록
- Windows Smart App Control (SAC) 환경에서 즉시 차단 없이 정상 실행됨을 확인할 수 있습니다.
