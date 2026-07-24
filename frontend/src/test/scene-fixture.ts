import type { SceneComponent, ScenePayload } from '@/api'

const components: SceneComponent[] = [
  {
    object_id: 1,
    component_id: 1,
    object_name: 'STEP Solid 1',
    component_name: 'STEP Solid 1',
    face_indices: [0, 1, 2],
    face_count: 3,
    area_mm2: 1200,
    bbox_min: [0, 0, 0],
    bbox_max: [60, 60, 10],
    is_truncated: false,
  },
  {
    object_id: 2,
    component_id: 2,
    object_name: 'STEP Solid 2',
    component_name: 'STEP Solid 2',
    face_indices: [3, 4],
    face_count: 2,
    area_mm2: 480,
    bbox_min: [5, 5, 10],
    bbox_max: [55, 55, 20],
    is_truncated: false,
  },
]

export function createSceneFixture(): ScenePayload {
  return {
    schema_version: 'mesh-scene.v1',
    units: { length: 'mm' },
    coordinate_system: {
      handedness: 'right',
      axes: {
        x: 'model_x',
        y: 'model_y',
        z: 'model_z',
      },
    },
    mesh: {
      vertices: [],
      faces: [],
      face_ids: [],
      face_component_ids: [],
      face_material_ids: [],
      face_normals: [],
      face_centroids: [],
      face_areas_mm2: [],
      feature_edge_segments: [],
    },
    objects: components,
    components,
    metadata: {
      face_count: 5,
      vertex_count: 12,
      component_count: 2,
      source_file: 'fixture.step',
      synthetic: false,
      import_note: 'Test fixture',
      receiver_face_hint: [],
      scene_token: 'fixture-token',
    },
  }
}
