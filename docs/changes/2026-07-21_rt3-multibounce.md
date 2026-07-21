# 2026-07-21 RT-3 다회 반사 구현

## 변경 목적
- RT-2C의 최대 1회 반사를 반복 가능한 bounce loop로 확장한다.
- 작은 Gap 내부에서 여러 부품을 연속 반사한 뒤 외부로 누설되는 경로를 계산한다.
- 저에너지 ray를 종료해 정확도와 계산 시간을 조절한다.

## Backend 구현
- `max_depth=0~3` 설정에 따라 반사 횟수를 제한한다.
- 각 bounce마다 Receiver와 가장 가까운 CAD surface를 다시 비교한다.
- 충돌 face의 optical profile을 매번 다시 조회하고 반사율과 산란 모델을 적용한다.
- `threshold`와 `russian_roulette` termination mode를 지원한다.
- 저장 ray path에 bounce depth, 입사 power, 출사 power를 기록한다.
- 직접광·반사광의 기존 RT-2D 기여도 필드를 유지하면서 depth별 집계를 추가한다.

## UI 구현
- Web UI 버전을 `v0.9.12`로 변경했다.
- Advanced에 `Max reflections`, `Termination`, `Min ray power` 입력을 추가했다.
- 결과 영역을 one-bounce 문구에서 multi-bounce 문구로 변경했다.
- 반사 결과에 max depth와 다음 surface로 계속 진행한 ray 수를 표시한다.

## 검증
- RT-3 전용 합성 회귀 테스트 5개를 추가했다.
- 전체 회귀 테스트 43개가 통과했다.
- 2회 반사가 필요한 합성 모델에서 `max_depth=1`은 0 hit, `max_depth=2`는 100% hit를 기록했다.
- 반사율 `0.8 × 0.5` 적용 후 Receiver flux가 예상값 `0.4 lumen`과 일치했다.
- Russian roulette 검증에서 80.4% ray가 생존하고 Receiver flux는 `0.402 lumen`으로 기대값을 유지했다.

## 성능
- 다회 반사와 depth 집계를 추가한 뒤 100,000 Gaussian ray는 약 `2.53초`였다.
- 1,000,000 Gaussian ray는 약 `25.09초`, 약 `39,850 rays/s`였다.
- RT-2D-A 기준 약 `2.18초`보다 증가했으며, 다회 bounce와 depth 집계 비용이 포함된 결과다.
- depth dictionary의 불필요한 반복 생성을 제거해 초기 RT-3 측정 `2.96초`에서 개선했다.

## 시각 리포트
- `docs/rt3-multibounce-validation.md`
- `docs/reports/rt3_multibounce/rt3_multibounce_report.html`
- `docs/reports/rt3_multibounce/rt3_multibounce_validation.png`
