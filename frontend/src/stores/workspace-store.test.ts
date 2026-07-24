import { describe, expect, it } from 'vitest'

import { createWorkspaceStore } from './workspace-store'

describe('workspace store', () => {
  it('normalizes selection IDs and supports toggling', () => {
    const store = createWorkspaceStore()
    const { actions } = store.getState()

    actions.setSelectedFaceIds([5, 2, 5, -1, 1.5, 0])
    expect(store.getState().selectedFaceIds).toEqual([0, 2, 5])

    actions.toggleSelectedFaceId(2)
    actions.toggleSelectedFaceId(3)
    expect(store.getState().selectedFaceIds).toEqual([0, 3, 5])
  })

  it('resets scene-scoped state when the active CAD changes', () => {
    const store = createWorkspaceStore()
    const { actions } = store.getState()

    actions.setActiveCad({
      path: 'C:\\uploads\\first.step',
      displayName: 'first.step',
    })
    actions.setSelectedComponentIds([1, 2])
    actions.setHiddenComponentIds([3])
    actions.setExcludedComponentIds([4])
    actions.setDeletedComponentIds([5])
    actions.setActiveRayTraceJobId('job-1')

    actions.setActiveCad({
      path: 'C:\\uploads\\second.step',
      displayName: 'second.step',
    })

    expect(store.getState()).toMatchObject({
      activeCad: {
        path: 'C:\\uploads\\second.step',
        displayName: 'second.step',
      },
      selectedComponentIds: [],
      hiddenComponentIds: [],
      excludedComponentIds: [],
      deletedComponentIds: [],
      activeRayTraceJobId: null,
    })
  })

  it('can clear scene state without forgetting the active CAD', () => {
    const store = createWorkspaceStore()
    const { actions } = store.getState()
    const cad = {
      path: 'C:\\uploads\\frame.step',
      displayName: 'frame.step',
    }

    actions.setActiveCad(cad)
    actions.setSelectedFaceIds([10])
    actions.setActiveRayTraceJobId('job-2')
    actions.clearSceneState()

    expect(store.getState().activeCad).toEqual(cad)
    expect(store.getState().selectedFaceIds).toEqual([])
    expect(store.getState().activeRayTraceJobId).toBeNull()
  })

  it('creates isolated stores for tests and future workspace instances', () => {
    const first = createWorkspaceStore()
    const second = createWorkspaceStore()

    first.getState().actions.setSelectedComponentIds([7])

    expect(first.getState().selectedComponentIds).toEqual([7])
    expect(second.getState().selectedComponentIds).toEqual([])
  })

  it('owns component, material, and transform feature state', () => {
    const store = createWorkspaceStore()
    const { actions } = store.getState()

    actions.renameComponent(2, 'Chassis rear')
    actions.toggleComponentVisibility(2)
    actions.toggleComponentTraceability(2)
    actions.upsertMaterialAssignment({
      assignmentId: 'material-part-2',
      componentId: 2,
      targetType: 'part',
      faceIds: [],
      baseMaterialId: 'black_pc_resin',
      surfaceId: 'matte_black_resin',
      profileId: '',
      bsdfAssetId: '',
      enabled: true,
    })
    actions.upsertTransformRule({
      ruleId: 'transform-component-2',
      componentId: 2,
      targetType: 'component',
      selectionMethod: 'click',
      faceIds: [],
      move: { x: 1, y: 2, z: 3 },
      tilt: { x: 0, y: 0, z: 5 },
      enabled: true,
    })

    expect(store.getState()).toMatchObject({
      componentNameOverrides: { 2: 'Chassis rear' },
      hiddenComponentIds: [2],
      excludedComponentIds: [2],
    })
    expect(store.getState().materialAssignments).toHaveLength(1)
    expect(store.getState().transformRules).toHaveLength(1)

    actions.deleteComponent(2, [3, 4])

    expect(store.getState()).toMatchObject({
      deletedComponentIds: [2],
      hiddenComponentIds: [],
      excludedComponentIds: [],
      materialAssignments: [],
      transformRules: [],
    })
  })
})
