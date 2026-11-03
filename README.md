# G1UltraMetal

Apple Metal on the Arm Mali-G1 Ultra (Mali arch v14, MediaTek MT6993, OPPO Find X9 /
PLJ110) for the iOS 16 port in [ios_plj110](https://github.com/tosasitill/ios_plj110).
CoreAnimation and other system clients use ordinary `MTLDevice` APIs; this stack
translates them to Vulkan with metal2vulkan and runs them on Mesa's PanVK (CSF, v14)
over a native X9 kernel transport instead of Linux DRM/panthor.

```
Metal client (QuartzCore, SpringBoard, ...)
  -> metal/General   X9GeneralMetal<N>.bundle  (Metal frontend, bridge, captures)
  -> metal2vulkan    Metal/AIR -> Vulkan/SPIR-V  (patched, build/third_party/metal2vulkan-pan205)
  -> PanVK v14       Mesa 300b5fd + build/third_party/00..11  -> X9PanVK<N>.bundle
  -> metal/General/panvk  X9 native kmod: memory, sync, tiler heap, submit (no DRM)
  -> ios_plj110 kernel   SweetX9 render service / CSF firmware queue
```

## Layout

| Path | Contents |
|---|---|
| `metal/` | X9 Metal frontend (`General/`), native bridge (`General/bridge`), PanVK backend (`General/panvk`), probes |
| `build/build.py` | Plugin build entrypoint (PanVK, GeneralMetal, mailbox package, kernel allowlist header) |
| `build/scripts/` | Build steps (configure/patch/compile/package) |
| `build/third_party/` | Mesa patches `00`..`11`, metal2vulkan patches |
| `docs/` | Design notes and rendering investigations |

Kernel, boot image, mailbox updater and device tools stay in ios_plj110.

## Workspace

The third-party trees are not in git. `build/prepare-local.py` expects them under
`.local/x9/work/x9-metal-render/` (`mesa-source`, `mesa-render-source`,
`metal2vulkan-pan205-source`, `libdrm-2.4.133`; pins in `build/local-source-lock.json`)
and links `.local/x9/MaliMetal/X9/General` to `metal/General`. On the build Mac the
existing tree is ios_plj110's `.local`; share it with `ln -s ~/ios_plj110/.local .local`
(both repos then relink the same `MaliMetal` path, so build from one at a time).

`00-mesa-panvk-x9.patch` is already applied in that `mesa-render-source`; its meson
paths name `/Users/tosasitill/ios_plj110/.local/...`. A fresh Mesa checkout needs those
paths adjusted before applying it.

Copy `build/local.example.json` to `build/local.json`. Xcode 15 must be the active
developer directory (`sudo xcode-select -s .../Xcode.app/Contents/Developer`); the PanVK
script pins the iPhoneOS / MacOSX SDK for Rust links itself.

## Build

```
python3 -I build/build.py --revision 243 --name rev243
```

Produces `out/rev243/plugin-package/` (stage with ios_plj110 `x9/mailbox/update.py`) and
`out/rev243/x9_render_external_manifest.h` (copy to ios_plj110
`x9/kernel/generated/` before building the matching kernel).

## Notable fixes

- Partial final IDVS vertex group (`docs/partial-vertex-group.md`): non-indexed triangle
  lists whose vertex count is not a multiple of 4 misplace their last vertex on the
  G1 Ultra; the frontend pads them (default on, boot token `x9p0` disables). This removed
  the diagonal split on Control Center platters.
- Tiler heap A/B (`x9tb`/`x9vt`): backboardd 128 MiB, others 32 MiB.

## License

X9 code: MIT (`LICENSE`). Patches under `build/third_party` follow the licenses of the
projects they modify (Mesa: MIT; metal2vulkan: see upstream).
