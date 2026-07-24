import type { SceneComponent } from '@/api'

export function getComponentDisplayName(
  component: SceneComponent,
  nameOverrides: Record<number, string>,
): string {
  return (
    nameOverrides[component.component_id] ||
    component.component_name ||
    component.object_name ||
    `Component ${component.component_id}`
  )
}

export function formatArea(areaMm2: number): string {
  return new Intl.NumberFormat('en-US', {
    maximumFractionDigits: 1,
  }).format(areaMm2)
}
