# TV 빛샘 테스트용 STEP 샘플 모델

## 목적
- 실제 사내 도면 없이도 CAD import, ROI 선택, component transform, ray tracing 입력 설정을 테스트하기 위한 단순 TV 기구 샘플이다.
- 실제 TV 전체 형상을 정밀하게 재현하는 것이 아니라, 하단 코너 빛샘 구조를 이해하고 기능 검증하기 위한 baseline 모델이다.

## 생성 파일
- `samples/tv_leakage_full_assembled_no_gap.stp`
  - 전체 TV 형상 baseline
  - 크기: `800 x 450 x 45 mm`
  - 추후 ROI 설정 테스트용
- `samples/tv_leakage_roi_left_bottom_no_gap.stp`
  - 좌측 하단 코너 ROI 단순 모델
  - 크기: `60 x 60 x 45 mm`
  - ray tracing 실험용
- `samples/tv_leakage_roi_right_bottom_no_gap.stp`
  - 우측 하단 코너 ROI 단순 모델
  - 크기: `60 x 60 x 45 mm`
  - ray tracing 실험용
- `samples/tv_leakage_sample_models_metadata.json`
  - 좌표계, 부품명, 생성 의도, 추천 emitter/receiver 후보 설명

## 부품 구성
- `Chassis_Rear`
  - TV 후면 기준 구조물
  - rear plate, bottom hemming, side wall을 단순 box 조합으로 표현
- `LCD_Cell_3T`
  - 두께 `3 mm`의 LCD Cell 단순 평판
- `Frame_Middle_FMB`
  - LCD Cell을 아래에서 받치는 frame middle 구조물
- `Cover_Deco`
  - 하단/측면 외장 deco
  - FMB와 LCD Cell을 가리는 전면부 cover 역할

## 좌표계
- 단위: `mm`
- `X`: TV 좌우 방향
- `Y`: TV 하단에서 상단 방향
- `Z`: TV 후면에서 전면 방향

## Gap 상태
- 현재 모델은 의도적인 gap이 없는 `no-gap assembled baseline`이다.
- gap 테스트는 simulator의 component transform 기능으로 `Cover_Deco`, `Frame_Middle_FMB`, `Chassis_Rear` 등을 이동시켜 만든다.
- 예:
  - `Cover_Deco`를 `Z +0.2 mm` 이동
  - `Frame_Middle_FMB`를 `Y -0.1 mm` 이동
  - `Cover_Deco`에 `Rx/Ry/Rz` tilt 적용

## Ray tracing 사용 힌트
- ROI 모델에서 먼저 실험하는 것을 추천한다.
- emitter 후보:
  - `Chassis_Rear` 내부 하단 hemming 주변
  - `Frame_Middle_FMB` 뒤쪽/아래쪽과 맞닿는 면
- receiver 후보:
  - `Cover_Deco` 외부 전면/하단 seam 근처
  - 사용자가 TV를 보는 방향 쪽에 작은 rectangular receiver 배치
- RT-1은 direct receiver hit만 계산하므로, 반사 기반 경로는 RT-2 이후에 확인한다.

## 재생성 방법
```powershell
.\_tools\python313\python.exe samples\generate_tv_leakage_test_models.py
```

## Import 검증 결과
- `tv_leakage_full_assembled_no_gap.stp`
  - synthetic: `False`
  - faces: `116`
  - vertices: `64`
  - objects/components: `3`
- `tv_leakage_roi_left_bottom_no_gap.stp`
  - synthetic: `False`
  - faces: `88`
  - vertices: `51`
  - objects/components: `4`
- `tv_leakage_roi_right_bottom_no_gap.stp`
  - synthetic: `False`
  - faces: `88`
  - vertices: `51`
  - objects/components: `4`
