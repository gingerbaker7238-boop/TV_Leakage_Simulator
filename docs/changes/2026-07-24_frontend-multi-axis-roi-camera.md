# Frontend multi-axis camera and ROI

## 요구사항

- ROI 완료 후 결과를 임의 Iso나 새 `Fit` 화면으로 바꾸지 않고 선택 전
  카메라 화면을 그대로 유지한다.
- 카메라와 박스 ROI 모두 `±XY`뿐 아니라 `±YZ`, `±ZX`를 지원한다.

## 구현

- 카메라 프리셋에 `YZ`, `-YZ`, `ZX`, `-ZX`를 추가했다.
- ROI를 무장할 때 현재 카메라와 가장 가까운 여섯 정면을 내적으로 찾는다.
- 선택 중에만 해당 정면을 사용하며 프리셋 버튼을 잠가 선택 평면이
  바뀌지 않게 한다.
- ROI 완료·취소·무결성 실패 시 저장한 position, controls target, up,
  near, far를 그대로 복원한다. ROI 결과에 맞춘 후속 `Fit`은 실행하지 않는다.
- `RoiClipBox`에 `xy`·`yz`·`zx` 투영 평면 계약과 Z 범위를 추가했다.
  기존 plane 없는 XY scope는 `xy`로 해석해 호환한다.
- face 교차 판정, Sutherland-Hodgman triangle clipping, T-junction 정리,
  section cap 삼각분할과 feature edge clipping을 세 평면 공통 로직으로
  일반화했다.

## 검증

- 단위 cube:
  - YZ와 ZX 절단 모두 cap 2개, 열린 chain 0개
  - 절단 좌표가 요청한 `0.25~0.75` 경계와 일치
- 실제 50,944-face, 4-component STEP:
  - 여섯 카메라 프리셋이 서로 다른 정면으로 전환
  - 임의 YZ 회전 화면 → ROI 선택 → 동일 카메라 화면 복원
  - `front_yz`: 24,381 triangles, cap 8개
  - `front_zx`: 29,343 triangles, cap 8개
  - `back_neg_yz`: 23,523 triangles, cap 8개
  - `back_neg_zx`: 21,584 triangles, cap 9개
- typecheck, lint, 9 test files·36 tests 통과
- 최신 브라우저 console error·warning 없음
