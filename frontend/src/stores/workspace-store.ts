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

        set((state) => ({
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
        }))
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
  activeRayTraceJobId: (state: WorkspaceStore) =>
    state.activeRayTraceJobId,
  actions: (state: WorkspaceStore) => state.actions,
}
