# 경량 STEP/STP 데스크톱 배포본

## 목적
- 회사 또는 사외 PC에 1.53GB 전체 `_tools` 폴더를 전달하지 않고 현재 시뮬레이터를 실행한다.
- 사용자가 명령어 없이 `LeakageSimulator.exe`를 더블클릭해 STP import와 ray tracing 기능을 시연한다.

## 결과물
- 폴더: `release/leakage_simulator_desktop_v0.9.10_lite/`
- ZIP: `release/leakage_simulator_desktop_v0.9.10_lite.zip`
- 체크섬: `release/leakage_simulator_desktop_v0.9.10_lite.zip.sha256`

## 경량화 결과
- 기존 전체 `_tools`: 약 `1.53GB`
- 기존 데스크톱 패키지: 약 `1.15GB`
- 경량 폴더: 약 `342.3MB`
- 경량 ZIP: 약 `94.9MB`

## 포함 런타임
- Python 3.13 embedded 기본 파일
- OCP Python module
- OCP가 실제로 연결하는 CAD/VTK DLL dependency closure
- NumPy와 NumPy native DLL
- WebView2 managed DLL

## 제외한 주요 패키지
- 전체 CadQuery Python package
- VTK Python modules
- SciPy
- Matplotlib
- Pillow
- PyArrow
- Jupyter
- llvmlite/Numba
- CasADi

## 포함된 시뮬레이터 상태
- Web UI `v0.9.10`
- STEP/STP import
- Three.js viewer
- ROI, Component, Transform
- Material/Optical property
- Emitter/Receiver
- RT-2A, RT-2B, RT-2C
- PERF-1 CPU hot path 최적화
- PERF-2 flat BVH CAD 교차 가속

## 빌드 자동화
- `build_lightweight_desktop.ps1`
- `build_lightweight_desktop.bat`
- `scripts/copy_pe_dependency_closure.py`

빌드 과정:
1. 최소 Python root 파일 복사
2. OCP와 NumPy 복사
3. PE import table을 분석해 필요한 native DLL만 복사
4. WebView2 desktop launcher 컴파일
5. 실제 STP import 검증
6. ray tracing test 34개 실행
7. ZIP 생성 및 필수 entry 검증
8. ZIP 재추출 후 OCP/STP 재검증
9. SHA-256 생성

## 검증 결과
- OCP import 성공
- NumPy `2.4.6` import 성공
- 샘플 STP import 결과 `synthetic=False`
- triangle `116`, vertex `64`, component `4`
- ray tracing unit test `34개` 통과
- 추출된 ZIP에서 Web UI health `v0.9.10` 확인

## 제한 사항
- X_T 직접 import는 현재 구현되지 않았다.
- matplotlib가 없으므로 legacy CLI PNG export는 생성되지 않을 수 있다.
- Web UI 내부 Receiver heatmap과 Three.js 결과 표시는 유지된다.
- WebView2 runtime이 없는 PC에서는 런처가 기본 브라우저 실행을 시도한다.

## 배포 방법
1. ZIP과 `.sha256` 파일을 함께 전달한다.
2. 대상 PC에서 ZIP을 완전히 압축 해제한다.
3. 폴더 구조를 변경하지 않는다.
4. `LeakageSimulator.exe`를 더블클릭한다.
