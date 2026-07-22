# Desktop EXE 서버 시작 타임아웃 개선

## 문제
- 회사 PC에서 `LeakageSimulator.exe` 실행 시 `The local web server did not become ready in time.` 오류가 발생했다.
- 기존 실행기는 45초 동안만 `127.0.0.1` health 응답을 기다렸다.
- 서버 시작 전에 OCP 네이티브 CAD DLL을 즉시 로드하여, 보안 프로그램 검사나 느린 디스크 환경에서 초기화가 오래 걸릴 수 있었다.
- 기존 오류창은 Python 프로세스 종료, CAD 런타임 지연, localhost 차단을 구분하기 어려웠다.

## 변경
- Web UI 버전을 `v0.9.11`로 변경했다.
- OCP와 CadQuery를 STEP/STP import 시점에 지연 로드하도록 변경했다.
- EXE 서버 실행에 `-u`와 `PYTHONUNBUFFERED=1`을 적용했다.
- 실행기 대기 시간을 45초에서 180초로 늘렸다.
- 10초마다 시작 진행 상황을 UI와 `desktop_runtime/launcher.log`에 기록한다.
- Python PID, 실행 경로, 조기 종료 코드, health 성공 여부를 기록한다.
- 선택한 포트와 실제 서버 포트가 달라지는 문제를 막기 위해 desktop 실행에서는 `--strict-port`를 사용한다.
- 빌드 후 압축 해제본에서 실제 웹 서버 health 검증을 자동 수행한다.
- 내장 WebView가 기본 브라우저로 불필요하게 우회되지 않도록 `WebView2Loader.dll`을 배포본에 포함한다.

## 원인 판별 기준
- `[BOOT] Embedded Python runtime started.`가 없으면 회사 보안 정책이 embedded Python 실행을 차단했을 가능성이 높다.
- 첫 `[BOOT]`만 있고 다음 단계가 오래 걸리면 Python module 또는 네이티브 DLL 검사가 지연되는 상황이다.
- `run web ui ...`가 기록되었는데 health가 실패하면 localhost 통신 차단 가능성이 높다.
- `Server process exited...`가 기록되면 해당 exit code와 직전 stderr가 직접 원인이다.

## 배포 파일
- `release/leakage_simulator_desktop_v0.9.11_lite.zip`
- 오류가 다시 발생하면 같은 폴더의 `desktop_runtime/launcher.log`만 전달하면 원인 분석이 가능하다.
