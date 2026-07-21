# 2026-07-21 RT-2D-A 기여도 계약 및 집계

## 변경 목적
- 직접광과 반사광을 명확히 분리한다.
- 빛샘 결과에 영향을 준 Receiver, component, face, material, 반사 lobe를 추적한다.
- 후속 UI와 보고서가 사용할 안정적인 backend 결과 계약을 만든다.

## 구현 내용
- `RayTraceContributionSummary`와 `rt-contribution.v1` 스키마를 추가했다.
- Receiver별 direct/reflected/total hit와 lumen을 집계한다.
- 최초 반사 면의 입사량, 반사 가능량, 반사 방출량, Receiver 도달량, 차단량, 이탈량을 집계한다.
- 실제 차폐한 두 번째 surface는 `secondary_block_*`로 별도 집계한다.
- component, face, material, specular/Lambertian/Gaussian lobe 기준 분해를 지원한다.
- 정식 결과 필드와 기존 metrics 호환 필드에 동일한 기여도 데이터를 직렬화한다.

## 성능 처리
- ray마다 component/material 중첩 dictionary를 갱신하지 않는다.
- 충돌 face만 tracing 중 희소 집계하고 component/material은 종료 후 합산한다.
- 1,000,000 Gaussian ray 실행 시간은 초기 RT-2D 구현의 약 `38.33초`에서 `21.49초`로 단축됐다.
- 현재 측정 처리량은 약 `46,533 rays/s`이며 기존 PERF-1/2 수준을 유지한다.

## 검증
- RT-2D 전용 테스트 4개 통과.
- 전체 회귀 테스트 38개 통과.
- 직접광 합계, 반사광 합계, component/face/material/lobe 분해를 검증했다.
- 반사 발생 면의 차단 결과와 실제 차폐 면의 기여도가 분리되는지 검증했다.

## 다음 단계
- RT-2D-B: 기여도 UI, 정렬/필터, 결과 보고서 연결.
- RT-2D 완료 후 RT-3에서 `max_depth=1~3` 다회 반사와 termination을 구현한다.
