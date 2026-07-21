# 2026-07-21 PERF-3A 단일 반사 Fast Path

## Backend
- `max_depth=0~1` 전용 `single_bounce_fast` 경로를 추가했다.
- `max_depth>=2`는 RT-3 `multi_bounce` 경로를 유지한다.
- `RayTraceConfig.contribution_mode`에 `summary`, `detailed`를 추가했다.
- performance summary에 `execution_path`, `contribution_mode`를 기록한다.

## Web UI
- Web UI 버전을 `v0.9.13`으로 변경했다.
- Ray Tracing Advanced에 `Result detail` 선택을 추가했다.
- 기본값은 `Fast summary`이며 필요할 때 `Detailed contribution`을 선택한다.

## 검증
- Fast summary와 Detailed contribution의 hit, flux, reflection summary, 저장 path가 동일함을 검증했다.
- 전체 회귀 테스트 `46개`가 통과했다.
- 백만 Gaussian ray 측정 결과:
  - Fast summary: `23.19초`, `43,122 rays/s`
  - Detailed contribution: `24.52초`, `40,783 rays/s`
  - 두 모드의 Receiver flux 차이: `0.0 lumen`

## 결과
- RT-3 최초 약 34% 성능 저하를 Fast summary 기준 약 7.9%까지 축소했다.
- 상세 보고서: `docs/perf3a-report.md`
