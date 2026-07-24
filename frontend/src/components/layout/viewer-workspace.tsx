import { useRef, useState } from 'react'
import type { SceneComponent, ScenePayload } from '@/api'
import {
  Box,
  BoxSelect,
  CircleDot,
  FileBox,
  LoaderCircle,
  Maximize2,
  Rotate3D,
} from 'lucide-react'

import {
  ComponentContextMenu,
  type ComponentContextAction,
} from '@/components/common'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import type { ComponentEditorRequest } from '@/features/components'
import { getComponentDisplayName } from '@/features/components'
import { cn } from '@/lib/utils'
import {
  useWorkspaceStore,
  workspaceSelectors,
} from '@/stores'

const cameraPresets = ['Fit', 'Iso', 'XY', '-XY'] as const
const renderModes = ['Wireframe', 'Surface', 'Surface + Edge'] as const

interface ViewerWorkspaceProps {
  scene?: ScenePayload
  isSceneLoading?: boolean
  sceneErrorMessage?: string
  onEditMaterial(request: ComponentEditorRequest): void
  onEditTransform(request: ComponentEditorRequest): void
  onDeleteComponent(request: ComponentEditorRequest): void
}

interface SceneComponentTileProps {
  component: SceneComponent
  displayName: string
  index: number
  selected: boolean
  visible: boolean
  traceable: boolean
  hasMaterial: boolean
  hasTransform: boolean
  onSelect(): void
  onAction(
    action: ComponentContextAction,
    returnFocusElement: HTMLElement | null,
  ): void
}

function SceneComponentTile({
  component,
  displayName,
  index,
  selected,
  visible,
  traceable,
  hasMaterial,
  hasTransform,
  onSelect,
  onAction,
}: SceneComponentTileProps) {
  const targetRef = useRef<HTMLButtonElement>(null)

  return (
    <ComponentContextMenu
      componentName={displayName}
      visible={visible}
      traceable={traceable}
      onAction={(action) => onAction(action, targetRef.current)}
    >
      <button
        ref={targetRef}
        type="button"
        data-testid={
          index === 0
            ? 'component-context-target'
            : `component-context-target-${component.component_id}`
        }
        aria-pressed={selected}
        className={cn(
          'group relative min-h-28 overflow-hidden rounded-xl border bg-card/72 p-3 text-left shadow-xl shadow-black/20 outline-none backdrop-blur transition-all focus-visible:ring-2 focus-visible:ring-primary',
          selected
            ? 'border-primary/65 bg-primary/12 shadow-primary/10'
            : 'border-border hover:border-primary/35 hover:bg-card',
          !visible && 'opacity-35 grayscale',
        )}
        onClick={onSelect}
      >
        <div
          className={cn(
            'absolute inset-0 opacity-15',
            index % 2 === 0
              ? 'bg-[linear-gradient(135deg,transparent_35%,var(--primary)_36%,transparent_37%,transparent_63%,var(--primary)_64%,transparent_65%)]'
              : 'bg-[radial-gradient(circle_at_70%_30%,var(--primary)_0,transparent_45%)]',
          )}
          aria-hidden="true"
        />
        <div className="relative flex items-start justify-between gap-3">
          <span
            className={cn(
              'flex size-8 shrink-0 items-center justify-center rounded-lg border',
              selected
                ? 'border-primary/40 bg-primary/15 text-primary'
                : 'border-border bg-background/45 text-muted-foreground',
            )}
          >
            <Box className="size-4" aria-hidden="true" />
          </span>
          <span className="flex flex-wrap justify-end gap-1">
            {!traceable ? (
              <Badge variant="outline" className="text-[0.55rem]">
                Trace off
              </Badge>
            ) : null}
            {hasMaterial ? (
              <Badge
                variant="outline"
                className="border-primary/25 text-[0.55rem] text-primary"
              >
                Material
              </Badge>
            ) : null}
            {hasTransform ? (
              <Badge
                variant="outline"
                className="border-warning/30 text-[0.55rem] text-warning"
              >
                Transform
              </Badge>
            ) : null}
          </span>
        </div>
        <div className="relative mt-4 truncate text-xs font-semibold">
          {displayName}
        </div>
        <div className="relative mt-1 text-[0.65rem] text-muted-foreground">
          {component.face_count.toLocaleString()} faces · ID{' '}
          {component.component_id}
        </div>
      </button>
    </ComponentContextMenu>
  )
}

export function ViewerWorkspace({
  scene,
  isSceneLoading = false,
  sceneErrorMessage,
  onEditMaterial,
  onEditTransform,
  onDeleteComponent,
}: ViewerWorkspaceProps) {
  const [cameraPreset, setCameraPreset] =
    useState<(typeof cameraPresets)[number]>('Iso')
  const [renderMode, setRenderMode] =
    useState<(typeof renderModes)[number]>('Wireframe')
  const [statusMessage, setStatusMessage] = useState(
    'CAD scene을 Import하면 Component Tree와 Viewer 상태가 연결됩니다.',
  )
  const selectedComponentIds = useWorkspaceStore(
    workspaceSelectors.selectedComponentIds,
  )
  const hiddenComponentIds = useWorkspaceStore(
    workspaceSelectors.hiddenComponentIds,
  )
  const excludedComponentIds = useWorkspaceStore(
    workspaceSelectors.excludedComponentIds,
  )
  const deletedComponentIds = useWorkspaceStore(
    workspaceSelectors.deletedComponentIds,
  )
  const nameOverrides = useWorkspaceStore(
    workspaceSelectors.componentNameOverrides,
  )
  const materialAssignments = useWorkspaceStore(
    workspaceSelectors.materialAssignments,
  )
  const transformRules = useWorkspaceStore(
    workspaceSelectors.transformRules,
  )
  const actions = useWorkspaceStore(workspaceSelectors.actions)

  const components = (scene?.components ?? []).filter(
    (component) => !deletedComponentIds.includes(component.component_id),
  )

  const handleContextAction = (
    component: SceneComponent,
    action: ComponentContextAction,
    returnFocusElement: HTMLElement | null,
  ) => {
    const componentId = component.component_id
    const request = { componentId, returnFocusElement }

    if (action === 'visibility') {
      const wasHidden = hiddenComponentIds.includes(componentId)
      actions.toggleComponentVisibility(componentId)
      setStatusMessage(
        `${getComponentDisplayName(component, nameOverrides)}를 ${wasHidden ? '표시' : '숨김'} 처리했습니다.`,
      )
    } else if (action === 'traceability') {
      const wasExcluded = excludedComponentIds.includes(componentId)
      actions.toggleComponentTraceability(componentId)
      setStatusMessage(
        `${getComponentDisplayName(component, nameOverrides)}의 Traceability를 ${wasExcluded ? '활성화' : '비활성화'}했습니다.`,
      )
    } else if (action === 'material') {
      onEditMaterial(request)
    } else if (action === 'transform') {
      onEditTransform(request)
    } else {
      onDeleteComponent(request)
    }
  }

  return (
    <main className="flex min-h-[42rem] min-w-0 flex-col bg-sim-viewer lg:min-h-0">
      <div className="border-b border-border bg-background/65 px-3 py-2.5">
        <div className="flex flex-wrap items-center justify-between gap-3">
          <div>
            <h1 className="text-sm font-semibold">3D Viewer</h1>
            <p className="text-[0.7rem] text-muted-foreground">
              Component state bridge · Three.js mesh connection in Step 08
            </p>
          </div>
          <div className="flex flex-wrap items-center gap-2">
            <div
              className="flex items-center gap-1 rounded-lg border border-border bg-background/60 p-1"
              aria-label="Camera presets"
            >
              {cameraPresets.map((preset) => (
                <Button
                  key={preset}
                  size="xs"
                  variant={cameraPreset === preset ? 'secondary' : 'ghost'}
                  aria-pressed={cameraPreset === preset}
                  onClick={() => {
                    setCameraPreset(preset)
                    setStatusMessage(`Camera preset · ${preset}`)
                  }}
                >
                  {preset === 'Fit' ? (
                    <Maximize2 aria-hidden="true" />
                  ) : null}
                  {preset}
                </Button>
              ))}
            </div>
            <div
              className="flex items-center gap-1 rounded-lg border border-border bg-background/60 p-1"
              aria-label="Render modes"
            >
              {renderModes.map((mode) => (
                <Button
                  key={mode}
                  size="xs"
                  variant={renderMode === mode ? 'secondary' : 'ghost'}
                  aria-pressed={renderMode === mode}
                  onClick={() => {
                    setRenderMode(mode)
                    setStatusMessage(`Render mode · ${mode}`)
                  }}
                >
                  {mode}
                </Button>
              ))}
            </div>
          </div>
        </div>
      </div>

      <div className="grid grid-cols-3 border-b border-border bg-background/40">
        {[
          ['Face', scene?.metadata.face_count.toLocaleString() ?? '0'],
          ['Vertex', scene?.metadata.vertex_count.toLocaleString() ?? '0'],
          [
            'Mode',
            scene ? (scene.metadata.synthetic ? 'Synthetic' : 'CAD') : '-',
          ],
        ].map(([label, value]) => (
          <div
            key={label}
            className="border-r border-border px-3 py-2 last:border-r-0"
          >
            <div className="text-[0.62rem] tracking-wide text-muted-foreground uppercase">
              {label}
            </div>
            <div className="mt-0.5 truncate text-xs font-semibold">
              {value}
            </div>
          </div>
        ))}
      </div>

      <div className="relative flex min-h-0 flex-1 p-3">
        <div className="relative flex min-h-[30rem] w-full items-center justify-center overflow-hidden rounded-xl border border-border bg-[radial-gradient(circle_at_center,var(--sim-panel-raised)_0,transparent_58%)] lg:min-h-0">
          <div
            className="pointer-events-none absolute inset-0 opacity-20"
            aria-hidden="true"
          >
            <div className="absolute inset-0 bg-[linear-gradient(to_right,var(--border)_1px,transparent_1px),linear-gradient(to_bottom,var(--border)_1px,transparent_1px)] bg-[size:32px_32px]" />
          </div>
          <div className="absolute top-3 left-3 z-10 flex items-center gap-2">
            <Badge
              variant="outline"
              className="border-border bg-background/70 text-muted-foreground backdrop-blur"
            >
              <Rotate3D data-icon="inline-start" />
              {cameraPreset}
            </Badge>
            <Badge
              variant="outline"
              className="border-border bg-background/70 text-muted-foreground backdrop-blur"
            >
              {renderMode}
            </Badge>
          </div>

          {isSceneLoading ? (
            <div className="relative z-10 flex flex-col items-center text-center">
              <LoaderCircle className="size-8 animate-spin text-primary" />
              <div className="mt-3 text-sm font-semibold">Loading CAD scene</div>
              <div className="mt-1 text-xs text-muted-foreground">
                Tessellation과 component metadata를 읽는 중입니다.
              </div>
            </div>
          ) : sceneErrorMessage ? (
            <div className="relative z-10 max-w-md rounded-xl border border-destructive/35 bg-destructive/8 p-4 text-center">
              <div className="text-sm font-semibold text-destructive">
                Scene load failed
              </div>
              <p className="mt-2 text-xs leading-5 text-muted-foreground">
                {sceneErrorMessage}
              </p>
            </div>
          ) : !scene ? (
            <div className="relative z-10 flex max-w-sm flex-col items-center px-6 text-center">
              <span className="flex size-14 items-center justify-center rounded-2xl border border-border bg-background/50 text-muted-foreground">
                <FileBox className="size-7" />
              </span>
              <div className="mt-4 text-sm font-semibold">Empty workspace</div>
              <p className="mt-1 text-xs leading-5 text-muted-foreground">
                왼쪽 Model import에서 CAD를 선택하면 실제 Component Tree가
                생성됩니다.
              </p>
            </div>
          ) : components.length === 0 ? (
            <div className="relative z-10 flex max-w-sm flex-col items-center px-6 text-center">
              <BoxSelect className="size-8 text-muted-foreground" />
              <div className="mt-3 text-sm font-semibold">
                No active components
              </div>
              <p className="mt-1 text-xs text-muted-foreground">
                삭제 상태를 복원하려면 CAD를 다시 Import하세요.
              </p>
            </div>
          ) : (
            <div className="relative z-10 grid w-[min(40rem,calc(100%-2rem))] grid-cols-1 gap-2 sm:grid-cols-2">
              {components.map((component, index) => {
                const componentId = component.component_id
                return (
                  <SceneComponentTile
                    key={componentId}
                    component={component}
                    displayName={getComponentDisplayName(
                      component,
                      nameOverrides,
                    )}
                    index={index}
                    selected={selectedComponentIds.includes(componentId)}
                    visible={!hiddenComponentIds.includes(componentId)}
                    traceable={!excludedComponentIds.includes(componentId)}
                    hasMaterial={materialAssignments.some(
                      (assignment) =>
                        assignment.componentId === componentId,
                    )}
                    hasTransform={transformRules.some(
                      (rule) => rule.componentId === componentId && rule.enabled,
                    )}
                    onSelect={() => {
                      actions.toggleSelectedComponentId(componentId)
                      setStatusMessage(
                        `Component selection · ${getComponentDisplayName(component, nameOverrides)}`,
                      )
                    }}
                    onAction={(action, returnFocusElement) =>
                      handleContextAction(
                        component,
                        action,
                        returnFocusElement,
                      )
                    }
                  />
                )
              })}
            </div>
          )}
        </div>
      </div>

      <footer className="flex min-h-9 items-center justify-between gap-3 border-t border-border bg-background/55 px-3 py-2 text-[0.68rem] text-muted-foreground">
        <span className="truncate">{statusMessage}</span>
        <span className="hidden shrink-0 items-center gap-1 sm:flex">
          <CircleDot className="size-3 text-primary" />
          {scene
            ? `${components.length} active · ${selectedComponentIds.length} selected`
            : 'Component bridge · Step 07'}
        </span>
      </footer>
    </main>
  )
}
