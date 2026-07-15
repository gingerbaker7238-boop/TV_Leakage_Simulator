# 2026-07-15 Component highlight / transform / viewer 조작 수정

## 배경
- Components 메뉴에서 객체를 선택해도 오른쪽 Three.js 3D viewer에서 선택 객체가 명확히 하이라이트되지 않았다.
- STEP import 후 component가 부품 전체가 아니라 CAD face 조각처럼 쪼개져 `부품 전체 이동`이 `면 이동`처럼 보이는 문제가 있었다.
- 3D viewer의 OrbitControls 설정이 명시적이지 않아 자유 회전 조작이 제한적으로 느껴졌다.

## 변경 사항
- Web UI version을 `v0.7.12`로 올렸다.
- Components 메뉴에서 선택한 객체들을 Three.js viewer overlay로 하이라이트하도록 변경했다.
  - 다중 선택 시 선택된 component가 모두 표시된다.
  - Material popup 대상 component도 별도 색상으로 표시된다.
- 적용 완료된 component transform rule은 현재 transform mode와 무관하게 계속 시각화되도록 변경했다.
- Three.js OrbitControls 설정을 명시했다.
  - left drag: rotate
  - middle wheel/drag: dolly
  - right drag: pan
  - polar angle 제한을 거의 전체 범위로 완화
- OCP STEP importer에서 face별로 중복 생성되던 vertex를 좌표 기준으로 dedupe했다.
  - 연결된 CAD face들이 같은 edge를 공유할 수 있어 component grouping이 부품/덩어리 단위에 더 가깝게 동작한다.
- 샘플 STEP 생성 스크립트의 assembly export mode를 `fused`에서 `default`로 바꿨다.
  - ROI 모델이 `Chassis / LCD Cell / FMB / Deco`에 대응되는 4개 component에 가깝게 분리된다.

## 원인 판단
- `부품 전체 이동`이 면 이동처럼 보인 주된 원인은 transform 수식 자체보다 STEP tessellation/import 단계에서 인접 face vertex가 공유되지 않아 component grouping이 과도하게 쪼개진 데 있었다.
- 즉, 도면 자체 문제라기보다 importer의 mesh 재구성 방식 문제가 컸다.

## 검증
- 샘플 STEP 모델 재생성:
  - `python samples/generate_tv_leakage_test_models.py`
- import checker:
  - 전체 TV 모델: faces `116`, vertices `64`, objects `3`
  - 좌측 ROI 모델: faces `88`, vertices `51`, objects `4`
  - 우측 ROI 모델: faces `88`, vertices `51`, objects `4`
- Python compile:
  - `run_web.py`
  - `src/leakage_simulator/importers.py`
  - `samples/generate_tv_leakage_test_models.py`

## 남은 한계
- STEP 원본 assembly/part 이름은 아직 완전히 보존하지 않는다.
- 전체 TV 모델은 부품들이 접촉/공유되는 구조 때문에 일부 component가 합쳐질 수 있다.
- 정확한 CAD assembly tree 보존은 추후 STEP label/name extraction 개선 항목으로 분리한다.
