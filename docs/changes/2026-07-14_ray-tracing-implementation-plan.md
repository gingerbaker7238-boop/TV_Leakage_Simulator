# 2026-07-14 Ray tracing 단계적 구현 계획

## 배경
- UI/Three.js viewer/transform/material library의 1차 골격이 갖춰졌기 때문에 다음 핵심 기능은 ray tracing이다.
- 빛샘 시뮬레이터는 LightTools 같은 범용 상용툴보다 가볍게 동작해야 하지만, 설계 의사결정에 필요한 상대/대략 절대 밝기 비교 정확도는 확보해야 한다.
- optical property는 ray hit 후 반사율, 흡수율, 산란 분포, receiver 누적 밝기 계산의 핵심 입력이 된다.

## 결정 사항
- 초기 ray tracing 엔진은 자체 구현으로 시작한다.
- 범용/상용 광학 엔진 연동은 보류한다.
- 계산은 ray-vector 기반으로 구현하되, 속도 병목이 확인되면 BVH/NumPy/Numba/Open3D/Embree 계열 가속을 단계적으로 검토한다.
- V1 emitter는 면 광원 기반으로 시작한다.
- emitter 입력은 normal 방향, lambertian/isotropic/gaussian 방향 분포, power lumen을 기본으로 한다.
- V1 receiver는 좌표/normal/size/resolution을 가지는 rectangular plane receiver로 시작한다.

## 추가 문서
- `docs/ray-tracing-design.md`

## 구현 Phase
- `RT-0`: 데이터 계약 고정
- `RT-1`: 면 emitter + direct receiver hit
- `RT-2`: 1회 반사 + optical property
- `RT-3`: 다중 bounce + termination
- `RT-4`: BVH/계산 가속
- `RT-5`: Web UI 연동
- `RT-6`: 실측 보정과 A/B 설계 비교

## 다음 작업
- `src/leakage_simulator/types.py` 또는 `src/leakage_simulator/raytracer.py`에 ray tracing dataclass를 추가한다.
- synthetic plane emitter/receiver 테스트 케이스를 만든다.
- direct ray hit 기반 receiver heatmap 출력부터 구현한다.
