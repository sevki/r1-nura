# postmarketOS on Rabbit R1

This repository contains the initial bring-up scaffold for a **postmarketOS
port to the Rabbit R1**. A pinned downstream kernel recipe is included; no
bootable image or hardware validation is available yet.

## Hardware baseline

- SoC: MediaTek MT6765 (platform name `k65v1_64_bsp`)
- Architecture: 64-bit ARM
- Memory: 4 GiB
- Display: 480 × 640 touchscreen
- Boot chain: MediaTek BROM → preloader → Little Kernel → boot image

The vendor kernel and stock boot container are references for running
postmarketOS on the hardware. They do not imply mainline kernel support.

## Included

- `device/testing/device-rabbit-r1/`: device APKBUILD and deviceinfo scaffold.
  It depends on `linux-rabbit-r1`; image generation is disabled
  until boot parameters have been confirmed.
- `device/testing/linux-rabbit-r1/`: vendor 4.19.191 recipe, generated config
  and compiler compatibility patch.
- `.github/workflows/`: automatic port checks and kernel/device package builds.
- `sources.json`: exact revisions of your packaging forks and hardware references.
- `tools/inspect_boot.py`: local, read-only inspection of boot container headers
  v0–v4, with optional component extraction into a new directory.
- `tests/`: synthetic boot-header tests. No hardware artifacts are included.
- `docs/bring-up.md`: source repositories, missing evidence, and kernel/boot
  validation milestones.

## Next milestone

Complete kernel compilation and package validation, then inspect a stock R1
boot image to establish the boot header and DTB/DTBO arrangement. See
[the bring-up guide](docs/bring-up.md) for the required inputs and validation gates. Kernel build completion, APK validation, firmware support,
boot integration and hardware testing are still pending.
