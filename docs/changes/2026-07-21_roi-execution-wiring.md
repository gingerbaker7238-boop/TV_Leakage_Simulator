# ROI를 실제 Ray Trace 실행에 연결 (지금까지는 미리보기 전용이었음)

## 배경
ROI 담당자가 Ray trace 담당자와 협의한 컨셉: **ROI를 지정하면 그 영역만 분석한다.**

그런데 확인해보니, 지금까지 웹 UI의 "실행" 버튼(`runDirectRayTrace()` → `POST /api/raytrace/direct`)이 부르는 실행 경로는 ROI를 전혀 몰랐다 - ROI를 아무리 골라도 항상 전체 모델로 시뮬레이션이 돌고 있었다. (`engine.py`의 `execute_run()`은 `roi_face_indices`를 이미 지원하지만, 그건 더 오래된 `/run`(폼 기반) 경로/CLI 전용이고, 웹 UI가 실제 쓰는 `raytrace_bridge.py` + `raytracer.py`의 `run_direct_ray_trace()` 파이프라인은 완전히 별개라 지금까지 ROI 필터가 없었다.)

## 변경 사항

### `src/leakage_simulator/raytrace_bridge.py`
- `filter_mesh_to_roi(mesh, roi_face_indices) -> (trimmed_mesh, face_remap)` 추가: 이미 transform이 적용된 mesh를 ROI face만 남기고 새로 만든다. `build_transformed_mesh()`가 각 face에 저장해두던 `"source_face_index"` 메타데이터(원본 scene mesh의 face index)를 이용해 "원본 face index → trim된 mesh의 face index" 매핑을 함께 반환한다.
- `build_direct_trace_input()`에 `request_payload["roi_faces"]` 처리 추가 - 값이 있으면 위 필터를 적용하고, 그 매핑으로 다음 두 곳의 face index를 다시 맞춰준다:
  - `EmitterSpec.face_indices` (`emitter_type == "face"`인 경우만): ROI 밖 face는 버리고, **전부** ROI 밖이면 명확한 에러(`... has no faces left inside the selected ROI`)를 낸다 - 조용히 0-face emitter가 되는 것을 막기 위함.
  - `OpticalAssignment.face_indices` (`target_type == "faces"`인 경우만): 여기는 다르게 처리 - 재질 override는 보통 ROI보다 훨씬 넓은 범위에 걸쳐 있는 게 정상이라, ROI 밖 face는 조용히 걸러내고(에러 아님) 남은 것만 적용한다.
  - `ReceiverSpec`은 원래 face index를 전혀 안 쓰는 가상 평면(center/normal/axis 기반)이라 remap 대상이 아님 - 확인 후 그대로 둠.
- `build_transformed_mesh()`의 시그니처/동작은 건드리지 않음 (기존 `tests/test_raytrace_bridge.py`의 2-인자 직접 호출 테스트가 그대로 통과) - ROI 필터링은 완전히 별도 단계로 추가.
- `roi_faces`가 없거나 빈 배열이면 필터링을 건너뛰고 기존과 100% 동일하게 동작 (하위 호환).

### `run_web.py`
- `runDirectRayTrace()`가 보내는 JSON payload에 `roi_faces: state.selectedFaces.size ? Array.from(state.selectedFaces) : undefined` 추가 - `state.selectedFaces`는 ROI List에서 체크된(활성) 항목들의 face를 모은 값 (`recomputeSelectedFaces()`가 채움 - `2026-07-20_roi-native-selection.md` 참고). 비어있으면 `undefined`라 `JSON.stringify`가 키 자체를 생략 - 서버가 "필터 없음"으로 인식해 기존과 동일하게 전체 모델을 씀.

## 자동 검증
- `tests/test_raytrace_bridge.py`에 `RoiFilteringTests` 추가 (5개, 전부 통과): ROI 없을 때 전체 mesh 유지, ROI 지정 시 mesh가 실제로 trim되고 face-emitter가 올바르게 remap됨, emitter가 ROI 밖으로 전부 밀려나면 명확한 에러, face 단위 optical assignment는 부분적으로만 걸러짐(에러 아님), 빈 roi_faces 배열은 필터 없음과 동일 취급.
- 기존 `RayTraceBridgeTests` 3개 전부 그대로 통과 (회귀 없음).
- 직접 `build_direct_trace_input()` → `run_direct_ray_trace()`까지 end-to-end 실행 확인: 2-face 씬에서 `roi_faces=[0]`을 주면 실제로 1-face mesh가 만들어지고, ray trace가 에러 없이 끝까지 실행됨.

## 현재 한계
- **브라우저 실사용 테스트 없음**: 이 연결은 Python 쪽 유닛 테스트 + 수동 end-to-end 스크립트로만 확인했다. 실제 웹 UI에서 ROI를 지정하고 "실행"을 눌렀을 때 결과가 정말 ROI 영역만 반영하는지는 아직 직접 확인 못 함 - 다음 브라우저 테스트에서 확인 필요.
- Face-type이 아닌 emitter(`datum_plane`/`reference_plane`, 가상 평면)는 ROI와 무관하게 그대로 살아있다 - 가상 평면 emitter가 ROI 바깥의 위치를 가리키고 있어도 지금은 막지 않는다 (물리적으로 "여기서 빛을 쏜다"는 의미라 ROI 안/밖 개념 자체가 애매함 - 필요하면 추후 논의).
- ROI 필터는 emitter/optical assignment의 **face 참조만** 다시 맞춘다 - Gap 규칙(`GapRule.target_face_indices`)이나 다른 파이프라인(`engine.py`의 `execute_run`, `/run` 경로)은 원래부터 별도의 `roi_faces` 처리 경로를 갖고 있어 이번 변경과 무관함.

## 상태
로컬 전용 구현. 팀 확인 + 브라우저 사용성 검증 완료 전까지 커밋/푸시하지 않음.
