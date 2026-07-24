import { useStore } from 'zustand'
import { createStore, type StoreApi } from 'zustand/vanilla'

export interface ActiveCad {
  path: string
  displayName: string
}

export interface Vector3Value {
  x: number
  y: number
  z: number
}

export type MaterialTargetType = 'part' | 'faces'

export interface MaterialAssignment {
  assignmentId: string
  componentId: number
  targetType: MaterialTargetType
  faceIds: number[]
  baseMaterialId: string
  surfaceId: string
  profileId: string
  bsdfAssetId: string
  enabled: boolean
}

export type TransformTargetType = 'component' | 'faces'
export type TransformSelectionMethod = 'click' | 'box'

export interface ComponentTransformRule {
  ruleId: string
  componentId: number
  targetType: TransformTargetType
  selectionMethod: TransformSelectionMethod
  faceIds: number[]
  move: Vector3Value
  tilt: Vector3Value
  enabled: boolean
}

export type RoiSelectionSource = 'box' | 'point'
export type RoiProjectionPlane = 'xy' | 'yz' | 'zx'
export type RoiView =
  | 'front_xy'
  | 'back_neg_xy'
  | 'front_yz'
  | 'back_neg_yz'
  | 'front_zx'
  | 'back_neg_zx'
  | 'coordinate'

export interface RoiClipBox {
  plane?: RoiProjectionPlane
  xMin: number
  xMax: number
  yMin: number
  yMax: number
  zMin?: number
  zMax?: number
}

export interface RoiComponentClip {
  componentId: number
  componentName: string
  faceIds: number[]
  areaMm2: number
  bboxMin: Vector3Value
  bboxMax: Vector3Value
}

export interface RoiScope {
  id: string
  scopeId: string
  source: RoiSelectionSource
  view: RoiView
  components: RoiComponentClip[]
  active: boolean
  clipBox?: RoiClipBox
  point?: Vector3Value
}

export interface RoiScopeInput {
  label?: string
  source: RoiSelectionSource
  view: RoiView
  components: RoiComponentClip[]
  clipBox?: RoiClipBox
  point?: Vector3Value
}

export interface WorkspaceSnapshot {
  activeCad: ActiveCad | null
  selectedFaceIds: number[]
  selectedComponentIds: number[]
  hiddenComponentIds: number[]
  excludedComponentIds: number[]
  deletedComponentIds: number[]
  componentNameOverrides: Record<number, string>
  materialAssignments: MaterialAssignment[]
  transformRules: ComponentTransformRule[]
  roiScopes: RoiScope[]
  roiScopeSequence: number
  roiBoxSelectionArmed: boolean
  roiDraftLabel: string
  activeRayTraceJobId: string | null
}

export interface WorkspaceActions {
  setActiveCad(cad: ActiveCad | null): void
  setSelectedFaceIds(faceIds: Iterable<number>): void
  toggleSelectedFaceId(faceId: number): void
  setSelectedComponentIds(componentIds: Iterable<number>): void
  toggleSelectedComponentId(componentId: number): void
  setHiddenComponentIds(componentIds: Iterable<number>): void
  setExcludedComponentIds(componentIds: Iterable<number>): void
  setDeletedComponentIds(componentIds: Iterable<number>): void
  toggleComponentVisibility(componentId: number): void
  toggleComponentTraceability(componentId: number): void
  renameComponent(componentId: number, name: string): void
  deleteComponent(componentId: number, faceIds?: Iterable<number>): void
  upsertMaterialAssignment(assignment: MaterialAssignment): void
  removeMaterialAssignment(assignmentId: string): void
  upsertTransformRule(rule: ComponentTransformRule): void
  setTransformRuleEnabled(ruleId: string, enabled: boolean): void
  removeTransformRule(ruleId: string): void
  addRoiScope(scope: RoiScopeInput): void
  setRoiScopeActive(scopeId: string, active: boolean): void
  removeRoiScope(scopeId: string): void
  clearRoiScopes(): void
  setRoiBoxSelectionArmed(armed: boolean): void
  setRoiDraftLabel(label: string): void
  setActiveRayTraceJobId(jobId: string | null): void
  clearSceneState(): void
  resetWorkspace(): void
}

export interface WorkspaceStore extends WorkspaceSnapshot {
  actions: WorkspaceActions
}

export type WorkspaceStoreApi = StoreApi<WorkspaceStore>

function normalizeIds(ids: Iterable<number>): number[] {
  return [...new Set(ids)]
    .filter((id) => Number.isSafeInteger(id) && id >= 0)
    .sort((left, right) => left - right)
}

function toggleId(ids: number[], id: number): number[] {
  if (!Number.isSafeInteger(id) || id < 0) {
    return ids
  }

  if (ids.includes(id)) {
    return ids.filter((item) => item !== id)
  }

  return normalizeIds([...ids, id])
}

function normalizeVector(vector: Vector3Value): Vector3Value {
  const normalizeValue = (value: number) =>
    Number.isFinite(value) ? value : 0

  return {
    x: normalizeValue(vector.x),
    y: normalizeValue(vector.y),
    z: normalizeValue(vector.z),
  }
}

function normalizeMaterialAssignment(
  assignment: MaterialAssignment,
): MaterialAssignment {
  return {
    ...assignment,
    faceIds: normalizeIds(assignment.faceIds),
  }
}

function normalizeTransformRule(
  rule: ComponentTransformRule,
): ComponentTransformRule {
  return {
    ...rule,
    faceIds: normalizeIds(rule.faceIds),
    move: normalizeVector(rule.move),
    tilt: normalizeVector(rule.tilt),
  }
}

function normalizeRoiComponentClip(
  component: RoiComponentClip,
): RoiComponentClip {
  return {
    ...component,
    faceIds: normalizeIds(component.faceIds),
    areaMm2: Number.isFinite(component.areaMm2)
      ? Math.max(component.areaMm2, 0)
      : 0,
    bboxMin: normalizeVector(component.bboxMin),
    bboxMax: normalizeVector(component.bboxMax),
  }
}

function normalizeRoiClipBox(
  clipBox: RoiClipBox | undefined,
): RoiClipBox | undefined {
  if (!clipBox) return undefined

  const plane = clipBox.plane ?? 'xy'
  const values =
    plane === 'xy'
      ? [clipBox.xMin, clipBox.xMax, clipBox.yMin, clipBox.yMax]
      : plane === 'yz'
        ? [clipBox.yMin, clipBox.yMax, clipBox.zMin, clipBox.zMax]
        : [clipBox.zMin, clipBox.zMax, clipBox.xMin, clipBox.xMax]
  if (values.some((value) => !Number.isFinite(value))) {
    return undefined
  }

  return {
    plane,
    xMin: Math.min(clipBox.xMin, clipBox.xMax),
    xMax: Math.max(clipBox.xMin, clipBox.xMax),
    yMin: Math.min(clipBox.yMin, clipBox.yMax),
    yMax: Math.max(clipBox.yMin, clipBox.yMax),
    zMin:
      clipBox.zMin === undefined || clipBox.zMax === undefined
        ? undefined
        : Math.min(clipBox.zMin, clipBox.zMax),
    zMax:
      clipBox.zMin === undefined || clipBox.zMax === undefined
        ? undefined
        : Math.max(clipBox.zMin, clipBox.zMax),
  }
}

function createSceneSnapshot(): Omit<WorkspaceSnapshot, 'activeCad'> {
  return {
    selectedFaceIds: [],
    selectedComponentIds: [],
    hiddenComponentIds: [],
    excludedComponentIds: [],
    deletedComponentIds: [],
    componentNameOverrides: {},
    materialAssignments: [],
    transformRules: [],
    roiScopes: [],
    roiScopeSequence: 0,
    roiBoxSelectionArmed: false,
    roiDraftLabel: '',
    activeRayTraceJobId: null,
  }
}

function createWorkspaceSnapshot(): WorkspaceSnapshot {
  return {
    activeCad: null,
    ...createSceneSnapshot(),
  }
}

export function createWorkspaceStore(): WorkspaceStoreApi {
  return createStore<WorkspaceStore>()((set) => ({
    ...createWorkspaceSnapshot(),
    actions: {
      setActiveCad: (activeCad) => {
        set({
          activeCad,
          ...createSceneSnapshot(),
        })
      },
      setSelectedFaceIds: (faceIds) => {
        set({ selectedFaceIds: normalizeIds(faceIds) })
      },
      toggleSelectedFaceId: (faceId) => {
        set((state) => ({
          selectedFaceIds: toggleId(state.selectedFaceIds, faceId),
        }))
      },
      setSelectedComponentIds: (componentIds) => {
        set({ selectedComponentIds: normalizeIds(componentIds) })
      },
      toggleSelectedComponentId: (componentId) => {
        set((state) => ({
          selectedComponentIds: toggleId(
            state.selectedComponentIds,
            componentId,
          ),
        }))
      },
      setHiddenComponentIds: (componentIds) => {
        set({ hiddenComponentIds: normalizeIds(componentIds) })
      },
      setExcludedComponentIds: (componentIds) => {
        set({ excludedComponentIds: normalizeIds(componentIds) })
      },
      setDeletedComponentIds: (componentIds) => {
        set({ deletedComponentIds: normalizeIds(componentIds) })
      },
      toggleComponentVisibility: (componentId) => {
        set((state) => ({
          hiddenComponentIds: toggleId(
            state.hiddenComponentIds,
            componentId,
          ),
        }))
      },
      toggleComponentTraceability: (componentId) => {
        set((state) => ({
          excludedComponentIds: toggleId(
            state.excludedComponentIds,
            componentId,
          ),
        }))
      },
      renameComponent: (componentId, name) => {
        if (!Number.isSafeInteger(componentId) || componentId < 0) return
        const normalizedName = name.trim()

        set((state) => {
          const componentNameOverrides = {
            ...state.componentNameOverrides,
          }

          if (normalizedName) {
            componentNameOverrides[componentId] = normalizedName
          } else {
            delete componentNameOverrides[componentId]
          }

          return { componentNameOverrides }
        })
      },
      deleteComponent: (componentId, faceIds = []) => {
        if (!Number.isSafeInteger(componentId) || componentId < 0) return
        const deletedFaceIds = new Set(normalizeIds(faceIds))

        set((state) => {
          const roiScopes = state.roiScopes
            .map((scope) => ({
              ...scope,
              components: scope.components.filter(
                (component) => component.componentId !== componentId,
              ),
            }))
            .filter((scope) => scope.components.length > 0)

          return {
            selectedFaceIds: state.selectedFaceIds.filter(
              (faceId) => !deletedFaceIds.has(faceId),
            ),
            selectedComponentIds: state.selectedComponentIds.filter(
              (id) => id !== componentId,
            ),
            hiddenComponentIds: state.hiddenComponentIds.filter(
              (id) => id !== componentId,
            ),
            excludedComponentIds: state.excludedComponentIds.filter(
              (id) => id !== componentId,
            ),
            deletedComponentIds: normalizeIds([
              ...state.deletedComponentIds,
              componentId,
            ]),
            materialAssignments: state.materialAssignments.filter(
              (assignment) => assignment.componentId !== componentId,
            ),
            transformRules: state.transformRules.filter(
              (rule) => rule.componentId !== componentId,
            ),
            roiScopes,
          }
        })
      },
      upsertMaterialAssignment: (assignment) => {
        const normalized = normalizeMaterialAssignment(assignment)
        set((state) => ({
          materialAssignments: [
            ...state.materialAssignments.filter(
              (item) => item.assignmentId !== normalized.assignmentId,
            ),
            normalized,
          ],
        }))
      },
      removeMaterialAssignment: (assignmentId) => {
        set((state) => ({
          materialAssignments: state.materialAssignments.filter(
            (assignment) => assignment.assignmentId !== assignmentId,
          ),
        }))
      },
      upsertTransformRule: (rule) => {
        const normalized = normalizeTransformRule(rule)
        set((state) => ({
          transformRules: [
            ...state.transformRules.filter(
              (item) => item.ruleId !== normalized.ruleId,
            ),
            normalized,
          ],
        }))
      },
      setTransformRuleEnabled: (ruleId, enabled) => {
        set((state) => ({
          transformRules: state.transformRules.map((rule) =>
            rule.ruleId === ruleId ? { ...rule, enabled } : rule,
          ),
        }))
      },
      removeTransformRule: (ruleId) => {
        set((state) => ({
          transformRules: state.transformRules.filter(
            (rule) => rule.ruleId !== ruleId,
          ),
        }))
      },
      addRoiScope: (scope) => {
        const components = scope.components
          .map(normalizeRoiComponentClip)
          .filter((component) => component.faceIds.length > 0)
        if (components.length === 0) return

        set((state) => {
          const sequence = state.roiScopeSequence + 1
          const label = scope.label?.trim()
          return {
            roiScopeSequence: sequence,
            roiDraftLabel: '',
            roiBoxSelectionArmed: false,
            roiScopes: [
              ...state.roiScopes,
              {
                id: `roi-${sequence}`,
                scopeId: label || `ROI-${sequence}`,
                source: scope.source,
                view: scope.view,
                components,
                active: true,
                clipBox: normalizeRoiClipBox(scope.clipBox),
                point: scope.point
                  ? normalizeVector(scope.point)
                  : undefined,
              },
            ],
          }
        })
      },
      setRoiScopeActive: (scopeId, active) => {
        set((state) => ({
          roiScopes: state.roiScopes.map((scope) =>
            scope.id === scopeId ? { ...scope, active } : scope,
          ),
        }))
      },
      removeRoiScope: (scopeId) => {
        set((state) => ({
          roiScopes: state.roiScopes.filter(
            (scope) => scope.id !== scopeId,
          ),
        }))
      },
      clearRoiScopes: () => {
        set({
          roiScopes: [],
          roiBoxSelectionArmed: false,
          roiDraftLabel: '',
        })
      },
      setRoiBoxSelectionArmed: (roiBoxSelectionArmed) => {
        set({ roiBoxSelectionArmed })
      },
      setRoiDraftLabel: (roiDraftLabel) => {
        set({ roiDraftLabel })
      },
      setActiveRayTraceJobId: (activeRayTraceJobId) => {
        set({ activeRayTraceJobId })
      },
      clearSceneState: () => {
        set(createSceneSnapshot())
      },
      resetWorkspace: () => {
        set(createWorkspaceSnapshot())
      },
    },
  }))
}

export const workspaceStore = createWorkspaceStore()

export function useWorkspaceStore<T>(
  selector: (state: WorkspaceStore) => T,
): T {
  return useStore(workspaceStore, selector)
}

export const workspaceSelectors = {
  activeCad: (state: WorkspaceStore) => state.activeCad,
  selectedFaceIds: (state: WorkspaceStore) => state.selectedFaceIds,
  selectedComponentIds: (state: WorkspaceStore) =>
    state.selectedComponentIds,
  hiddenComponentIds: (state: WorkspaceStore) => state.hiddenComponentIds,
  excludedComponentIds: (state: WorkspaceStore) =>
    state.excludedComponentIds,
  deletedComponentIds: (state: WorkspaceStore) =>
    state.deletedComponentIds,
  componentNameOverrides: (state: WorkspaceStore) =>
    state.componentNameOverrides,
  materialAssignments: (state: WorkspaceStore) =>
    state.materialAssignments,
  transformRules: (state: WorkspaceStore) => state.transformRules,
  roiScopes: (state: WorkspaceStore) => state.roiScopes,
  roiBoxSelectionArmed: (state: WorkspaceStore) =>
    state.roiBoxSelectionArmed,
  roiDraftLabel: (state: WorkspaceStore) => state.roiDraftLabel,
  activeRayTraceJobId: (state: WorkspaceStore) =>
    state.activeRayTraceJobId,
  actions: (state: WorkspaceStore) => state.actions,
}
