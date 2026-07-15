# Component Tree 이름 변경 UI 추가

## 배경
- STEP import 시 component 이름이 `STEP Solid 1`처럼 자동 생성되어 실제 부품명과 매칭하기 어렵다.
- Cover Deco, Chassis Rear, FMB, LCD Cell처럼 사용자가 이해하는 이름으로 component tree에서 바로 바꿀 수 있어야 한다.

## 변경 사항
- `run_web.py`
  - Web UI 버전을 `v0.7.15`로 갱신했다.
  - Components tree의 part 이름을 더블클릭하거나 `F2`를 눌러 inline rename할 수 있게 했다.
  - `Enter` 또는 blur 시 저장, `Escape` 시 취소한다.
  - 이름 변경 시 component tree, ROI component label, Transform manager rule label, Material assignment 표시를 함께 갱신한다.

## 현재 범위
- 이름 변경은 현재 브라우저 세션의 UI state에 반영된다.
- CAD를 다시 import하거나 페이지를 새로 로드하면 STEP 원본에서 가져온 기본 이름으로 돌아간다.
- 추후 scenario 저장/불러오기 기능을 만들 때 custom component name도 scenario 데이터에 포함해야 한다.

## 확인 방법
- STEP 파일을 import한다.
- Components tree에서 `STEP Solid 1` 같은 이름을 더블클릭하거나 포커스 후 `F2`를 누른다.
- 원하는 이름을 입력하고 `Enter`를 누른다.
- Transform popup, Transform manager, Material popup에서 변경된 이름이 함께 표시되는지 확인한다.
