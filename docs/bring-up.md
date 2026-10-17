# Rabbit R1 postmarketOS bring-up

## Current boundary

`device/testing/device-rabbit-r1` and `device/testing/linux-rabbit-r1` are
initial device and downstream kernel recipes for a pmaports checkout. The kernel
source and generated configuration are pinned; package build and hardware boot
validation are pending. Image generation and flashing are disabled. No partition
offsets or install commands are supplied.

## Source inputs

Exact reference commits are recorded in `sources.json`:

| Repository | Revision |
| --- | --- |
| https://github.com/sevki/pmaports | `f662ccdee08d3a37646e538238cdf0f271497c19` |
| https://github.com/sevki/pmbootstrap | `32e9aebe4336a852c199dfccd72159b1e88434a1` |
| https://github.com/rabbit-hmi-oss/android_kernel_rabbit_mt6765 | `8167c8c1087f057d2ef302fc93b47554291687ec` |
| https://github.com/DavidBuchanan314/rabbit_r1_boot_notes | `b1b35b1ea9023d7b38df407afb5911fd54287c2f` |

The network proxy issue has been resolved and all four sources were fetched.
pmbootstrap identifies itself as 3.10.1. The selected pmaports fork's branch is
`achill/phosh-syncbus`; it is intentionally pinned rather than tracking a moving
branch. pmbootstrap also requires `upstream/main:channels.cfg`, so CI fetches a
separately pinned upstream metadata revision from `sources.json` without changing
the fork checkout.

## Kernel evidence and current milestone

- Vendor kernel version: 4.19.191 (`Makefile`).
- Candidate board configuration: `arch/arm64/configs/k65v1_64_bsp_defconfig`.
- The matching `arch/arm64/boot/dts/mediatek/k65v1_64_bsp.dts` is a **plugin
  overlay**, not a standalone board tree. It includes Hynitron touchscreen
  coordinates of 480 × 640 and MS35774 motor nodes.
- `arch/arm64/boot/dts/mediatek/mt6765.dts` is the SoC base tree. The vendor's
  `kenv.mk` emits `Image.gz` and a separate SoC DTB. Final DTB/DTBO composition
  remains unverified; the kernel recipe does not append a guessed DTB.
- The committed full kernel config was generated with `k65v1_64_bsp_defconfig`,
  then updated for the pinned pmaports default kernel rules and regenerated with
  `olddefconfig`. Initramfs gzip and devtmpfs automount are enabled; IKHEADERS is
  disabled to avoid packaging debug headers. The postmarketOS default kconfig
  check passes. INPUT_EVDEV is built in (the checker prefers a module).
- A GCC 12 cross-build exposed vendor cross-translation-unit inline errors.
  The included patch changes the declarations and definitions of `uclamp_se_set`,
  `ksm_flock`, and `blk_crypto_flock` into ordinary external functions.
  Preparation also uses the
  standard downstream helper to remove vendor `-Werror` flags while preserving
  the existing compiler header (`REPLACE_GCCH=0`).

Local validation reached the real pmbootstrap/Alpine build, verified all source
checksums, applied the patch, and compiled past initial host-tool setup after
adding `linux-headers` to the recipe. Targeted compilation with Alpine GCC 15.2
passed for `block/blk-crypto.o`, `block/keyslot-manager.o`, `kernel/sched/tune.o`,
`kernel/sched/core.o` and `drivers/md/dm.o` with the final inline patch. The full
kernel build was stopped before completion; no complete kernel APK is claimed.
The first archive fetch in Alpine failed through the session proxy; the local
rehearsal used a pre-downloaded, checksum-verified copy in the distfiles cache.

A successful compiler or package build alone does not establish bootability.
The next boot integration input is a stock boot container from the target device,
recorded with its installed software version and SHA-256:

```sh
python3 tools/inspect_boot.py work/stock-boot.img --extract work/stock-boot
```

The inspector supports boot container versions 0–4 and rejects unsupported
wrappers. It reports header fields and copies components to a new directory. It
does not verify signatures, decompress kernels, or identify appended DTBs.
Versions 3–4 also require separate vendor_boot inspection. Do not infer boot
addresses, partition sizes or a complete board tree from an absent field.

## Follow-on gates

- Validate this device package with the fetched pmaports tooling and replace any
  fields required by the current schema. Add confirmed boot header parameters,
  offsets, command line, DTB arrangement and image limits to deviceinfo only
  after comparison with stock artifacts.
- Document required firmware names and redistribution terms. Add a reproducible
  local extraction or permitted packaging path based on actual driver requests.
- Establish a tested recovery route and determine whether temporary boot is
  supported on the target device. Do not assume standard fastboot boot works.
- Build a minimal postmarketOS initramfs/rootfs, then validate boot logs, display,
  input and storage on hardware. Capture results and recovery steps before any
  persistent installation workflow is introduced.

## Local verification

```sh
python3 -m unittest discover -s tests -v
sh -n device/testing/device-rabbit-r1/APKBUILD
sh -n device/testing/device-rabbit-r1/deviceinfo
```

Also run `python3 tools/fetch_sources.py` in a fresh workspace followed by
`python3 tools/check_port.py --pmbootstrap work/pmbootstrap --pmaports work/pmaports`.
The checker stages local packages into the disposable pmaports checkout and
validates metadata, local checksums, and the pinned default kernel rules.
These checks do not demonstrate kernel build or boot success.

## CI

`Port checks` runs on pushes and pull requests: inspector unit tests, shell
syntax, pmbootstrap package/device parsing, local source checksums and default
kernel config checks. `Kernel package build` runs for changes to device packages,
source pins, its helper scripts or workflow, and can also be run manually. It
uses pmbootstrap to build aarch64 kernel and device APKs, and retains build logs
and any APK outputs for 14 days, including logs from failed runs. Both workflows
have read-only repository permissions and pin their GitHub Actions revisions.

The kernel build has a two-hour limit and fails on build errors. CI does not
flash devices or claim hardware validation. No workflow has been run on GitHub
from this workspace yet.
