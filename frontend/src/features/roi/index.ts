export { RoiSelectionPanel } from './roi-selection-panel'
export {
  buildRoiClippedGeometries,
  clipTriangleToRoiBox,
  normalizeRoiClipBoxes,
  type RoiClippedGeometryBundle,
} from './roi-clipped-geometry'
export {
  getActiveRoiFaceIds,
  groupRoiFacesByComponent,
  resolveFacesInRoiBox,
  resolveNearestVisibleFace,
  summarizeActiveRoiScopes,
  triangleIntersectsRoiBox,
} from './roi-selection'
