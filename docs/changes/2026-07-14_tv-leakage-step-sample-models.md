# 2026-07-14 TV 빛샘 STEP 샘플 모델 생성

## 배경
- 실제 사내 TV 도면 없이 CAD import, ROI 선택, component transform, ray tracing 설정을 테스트할 수 있는 단순 샘플이 필요했다.
- 사용자가 제공한 PPT 구조 설명을 기준으로 `Chassis Rear`, `LCD Cell`, `Frame Middle`, `Cover Deco`의 조립 관계를 단순화했다.
- 실제 빛샘 ROI는 TV 하단 좌/우 코너의 약 `50 x 50 x 50 mm^3` 영역이므로, 전체 모델과 ROI 모델을 분리해 생성했다.

## 추가 파일
- `samples/generate_tv_leakage_test_models.py`
- `samples/tv_leakage_full_assembled_no_gap.stp`
- `samples/tv_leakage_roi_left_bottom_no_gap.stp`
- `samples/tv_leakage_roi_right_bottom_no_gap.stp`
- `samples/tv_leakage_sample_models_metadata.json`
- `samples/tv_leakage_sample_models.md`

## 모델 구성
- 전체 TV baseline:
  - `800 x 450 x 45 mm`
  - ROI 선택 테스트용
- 좌측 하단 ROI:
  - `60 x 60 x 45 mm`
  - ray tracing 실험용
- 우측 하단 ROI:
  - `60 x 60 x 45 mm`
  - ray tracing 실험용

## 부품
- `Chassis_Rear`
- `LCD_Cell_3T`
- `Frame_Middle_FMB`
- `Cover_Deco`

## Gap 조건
- 현재 STEP 모델은 의도적인 gap이 없는 `no-gap assembled baseline`이다.
- gap은 이후 simulator의 component transform 기능으로 생성한다.

## 검증
실행 명령:

```powershell
.\_tools\python313\python.exe samples\generate_tv_leakage_test_models.py
.\_tools\python313\python.exe check_cad_import.py --cad samples\tv_leakage_full_assembled_no_gap.stp
.\_tools\python313\python.exe check_cad_import.py --cad samples\tv_leakage_roi_left_bottom_no_gap.stp
.\_tools\python313\python.exe check_cad_import.py --cad samples\tv_leakage_roi_right_bottom_no_gap.stp
```

결과:
- 전체 모델 import 성공
  - synthetic: `False`
  - faces: `116`
  - vertices: `64`
  - objects/components: `4`
- 좌측 ROI 모델 import 성공
  - synthetic: `False`
  - faces: `88`
  - vertices: `51`
  - objects/components: `4`
- 우측 ROI 모델 import 성공
  - synthetic: `False`
  - faces: `88`
  - vertices: `51`
  - objects/components: `4`

## 다음 작업
- Web UI에서 전체 모델을 import하여 ROI 선택 동작을 확인한다.
- ROI 모델에서 emitter/receiver 배치 UI를 붙인 뒤 RT-1 direct ray tracing을 시각화한다.
- RT-2에서 FMB/Cover Deco/Chassis Rear 반사와 optical property 감쇄를 붙인다.
