import { describe, expect, it } from 'vitest'

import { createSceneFixture } from '@/test/scene-fixture'

import {
  createComponentGeometry,
  createFeatureEdgeGeometry,
  getSceneBounds,
} from './scene-geometry'

describe('Three.js scene geometry', () => {
  it('builds component-local triangles with stable source face ids', () => {
    const scene = createSceneFixture()
    const bundle = createComponentGeometry(scene, scene.components[0])
    const position = bundle.geometry.getAttribute('position')

    expect(position.count).toBe(9)
    expect(bundle.faceIds).toEqual([0, 1, 2])
    expect(bundle.geometry.userData.sourceFaceIds).toEqual([0, 1, 2])
    expect(bundle.center.toArray()).toEqual([30, 30, 5])
    expect([position.getX(0), position.getY(0), position.getZ(0)]).toEqual([
      -30,
      -30,
      -5,
    ])

    bundle.geometry.dispose()
  })

  it('builds clean feature edge segments in component-local space', () => {
    const scene = createSceneFixture()
    const bundle = createComponentGeometry(scene, scene.components[0])
    const geometry = createFeatureEdgeGeometry(
      scene.mesh.feature_edge_segments.filter(
        (segment) => segment.component_id === 1,
      ),
      bundle.center,
    )
    const position = geometry.getAttribute('position')

    expect(position.count).toBe(2)
    expect([position.getX(0), position.getY(0), position.getZ(0)]).toEqual([
      -30,
      -30,
      -5,
    ])
    expect([position.getX(1), position.getY(1), position.getZ(1)]).toEqual([
      30,
      -30,
      -5,
    ])

    geometry.dispose()
    bundle.geometry.dispose()
  })

  it('derives a stable fit-to-view bounding box', () => {
    const bounds = getSceneBounds(createSceneFixture())

    expect(bounds.center.toArray()).toEqual([30, 30, 10])
    expect(bounds.size.toArray()).toEqual([60, 60, 20])
  })
})
