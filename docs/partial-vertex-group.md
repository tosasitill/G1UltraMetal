# Last vertex misplaced in partial IDVS vertex groups (Mali-G1 Ultra, v14)

Observed 2026-11-03 on PLJ110 (MT6993), Mesa PanVK 300b5fd (CSF, arch 14), driven by
CoreAnimation through metal2vulkan.

## Symptom

Control Center platters (non-indexed `MTLPrimitiveTypeTriangle`, 9 vertices: one
zero-area triangle and two that form a rectangle) showed a diagonal split: one half
missing or with different colours.

## Evidence (in-process GPU replays, ios_plj110 rev237-241)

- The same draw replayed 14-24 times in one command buffer, each pass in its own
  box-sized target: identical inputs (also frozen CPU snapshots) gave different output
  hashes. Coverage maps showed tri2 drawn with its LAST vertex displaced by a varying
  amount; the other vertices were correct.
- 12- and 24-vertex draws never failed; 6- and 9-vertex draws did.
- The same draw padded with copies of its last vertex (zero-area triangles) to 12, 24
  or 48 vertices gave one hash over all repeats, with coverage exactly matching the
  CPU projection. Unpadded output also drew samples outside the rectangle.
- Tiler heap size (10, 32, 128 MiB) and BIR vs Kraid compiler made no difference.
  PanVK writes `INDEX_COUNT = vertex count` unchanged (csf `launch_draw`).

## Workaround

`metal/General/NativeBridgeMetalFrontend.mm` (`x9PadDraw`): non-indexed triangle lists
with `vertexStart == 0`, one instance and `count % 12 != 0` are drawn from inline
vertex bytes padded with copies of the last vertex to a multiple of 12, then the
app's bindings are restored. Boot token `x9p0` disables it.

## Open

Root cause (hardware lane masking in the last vertex group, firmware, or shared
lowering) is not localized. An upstream report needs a minimal Vulkan reproducer:
`vkCmdDraw(cmd, 9, 1, 0, 0)` with a distinct last vertex, read back the target
repeatedly.
