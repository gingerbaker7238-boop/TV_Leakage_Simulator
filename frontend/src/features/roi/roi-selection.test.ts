import { describe, expect, it } from 'vitest'

import { createSceneFixture } from '@/test/scene-fixture'
import type { RoiScope } from '@/stores'
import type { ScenePayload } from '@/api'

import { buildRoiClippedGeometries } from './roi-clipped-geometry'
import {
  getActiveRoiFaceIds,
  groupRoiFacesByComponent,
  resolveFacesInRoiBox,
  resolveNearestVisibleFace,
  summarizeActiveRoiScopes,
  triangleIntersectsRoiBox,
} from './roi-selection'

describe('ROI selection', () => {
  it('uses true triangle-to-box intersection instead of centroid only', () => {
    expect(
      triangleIntersectsRoiBox(
        [
          [0, 0],
          [100, 0],
          [0, 100],
        ],
        { xMin: 1, xMax: 2, yMin: 1, yMax: 2 },
      ),
    ).toBe(true)
    expect(
      triangleIntersectsRoiBox(
        [
          [0, 0],
          [5, 0],
          [0, 5],
        ],
        { xMin: 10, xMax: 12, yMin: 10, yMax: 12 },
      ),
    ).toBe(false)
  })

  it('selects XY-intersecting faces and excludes hidden components', () => {
    const scene = createSceneFixture()
    const box = { xMin: 58, xMax: 59, yMin: 1, yMax: 2 }

    expect(resolveFacesInRoiBox(scene, box, [])).toEqual([0, 2])
    expect(resolveFacesInRoiBox(scene, box, [1])).toEqual([])
  })

  it('groups ROI metadata by component and resolves coordinate input', () => {
    const scene = createSceneFixture()
    const components = groupRoiFacesByComponent(
      scene,
      [0, 3],
      { 2: 'Rear cover' },
    )

    expect(components).toHaveLength(2)
    expect(components[0]).toMatchObject({
      componentId: 1,
      faceIds: [0],
      areaMm2: 1800,
    })
    expect(components[1]).toMatchObject({
      componentId: 2,
      componentName: 'Rear cover',
      faceIds: [3],
      areaMm2: 1250,
    })
    expect(
      resolveNearestVisibleFace(
        scene,
        { x: 38, y: 22, z: 13 },
        [],
      ),
    ).toBe(3)
    expect(
      resolveNearestVisibleFace(
        scene,
        { x: 38, y: 22, z: 13 },
        [2],
      ),
    ).toBe(0)
  })

  it('merges only active ROI scopes into the analysis summary', () => {
    const scene = createSceneFixture()
    const componentOne = groupRoiFacesByComponent(scene, [0, 1])
    const componentTwo = groupRoiFacesByComponent(scene, [3])
    const scopes: RoiScope[] = [
      {
        id: 'roi-1',
        scopeId: 'ROI-1',
        source: 'box',
        view: 'front_xy',
        components: componentOne,
        active: true,
      },
      {
        id: 'roi-2',
        scopeId: 'ROI-2',
        source: 'point',
        view: 'coordinate',
        components: componentTwo,
        active: false,
      },
    ]

    expect(getActiveRoiFaceIds(scopes)).toEqual([0, 1])
    expect(summarizeActiveRoiScopes(scopes)).toMatchObject({
      scopeCount: 1,
      faceCount: 2,
      componentCount: 1,
      areaMm2: 3600,
    })
  })

  it('clips a closed solid at exact box planes and caps every section', () => {
    const cubeVertices: ScenePayload['mesh']['vertices'] = [
      [0, 0, 0],
      [1, 0, 0],
      [1, 1, 0],
      [0, 1, 0],
      [0, 0, 1],
      [1, 0, 1],
      [1, 1, 1],
      [0, 1, 1],
    ]
    const cubeFaces: ScenePayload['mesh']['faces'] = [
      [0, 2, 1],
      [0, 3, 2],
      [4, 5, 6],
      [4, 6, 7],
      [0, 1, 5],
      [0, 5, 4],
      [1, 2, 6],
      [1, 6, 5],
      [2, 3, 7],
      [2, 7, 6],
      [3, 0, 4],
      [3, 4, 7],
    ]
    const scene: ScenePayload = {
      ...createSceneFixture(),
      mesh: {
        vertices: cubeVertices,
        faces: cubeFaces,
        face_ids: cubeFaces.map((_, index) => index),
        face_component_ids: cubeFaces.map(() => 1),
        face_material_ids: cubeFaces.map(() => ''),
        face_normals: cubeFaces.map(() => [0, 0, 1]),
        face_centroids: cubeFaces.map(() => [0.5, 0.5, 0.5]),
        face_areas_mm2: cubeFaces.map(() => 0.5),
        feature_edge_segments: [],
      },
      components: [
        {
          ...createSceneFixture().components[0],
          face_indices: cubeFaces.map((_, index) => index),
          face_count: cubeFaces.length,
          bbox_min: [0, 0, 0],
          bbox_max: [1, 1, 1],
        },
      ],
      objects: [],
      metadata: {
        ...createSceneFixture().metadata,
        face_count: cubeFaces.length,
        vertex_count: cubeVertices.length,
        component_count: 1,
      },
    }
    scene.objects = scene.components

    const clipped = buildRoiClippedGeometries(
      scene,
      cubeFaces.map((_, index) => index),
      [{ xMin: 0.25, xMax: 0.75, yMin: -1, yMax: 2 }],
    )

    expect(clipped).not.toBeNull()
    expect(clipped?.openChainCount).toBe(0)
    expect(clipped?.capLoopCount).toBe(2)
    expect(clipped?.capGeometry).not.toBeNull()

    const positions = clipped?.surfaceGeometry.getAttribute('position')
    const xValues = Array.from(
      { length: positions?.count ?? 0 },
      (_, index) => positions?.getX(index) ?? 0,
    )
    expect(Math.min(...xValues)).toBeCloseTo(0.25)
    expect(Math.max(...xValues)).toBeCloseTo(0.75)

    clipped?.surfaceGeometry.dispose()
    clipped?.capGeometry?.dispose()
    clipped?.capEdgeGeometry?.dispose()
    clipped?.featureEdgeGeometry?.dispose()
  })
})
