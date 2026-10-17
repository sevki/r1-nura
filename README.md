# Nura on Rabbit R1

This repository is the starting point for bringing up Nura (formerly
postmarketOS) on the Rabbit R1. It does not yet contain a bootable image or a
device port.

## Hardware and boot baseline

- SoC: MediaTek MT6765 (platform name `k65v1_64_bsp`)
- Architecture: 64-bit ARM
- Memory: 4 GiB
- Display: 480 × 640 touchscreen
- Boot chain: MediaTek BROM → preloader → Little Kernel (LK) → Android boot
  image
- Existing device software: Android 13

Rabbit's [boot notes](https://github.com/DavidBuchanan314/rabbit_r1_boot_notes)
document the boot chain and include a device-tree dump. The
[Rabbit kernel source](https://github.com/rabbit-hmi-oss/android_kernel_rabbit_mt6765)
is a vendor 4.19 kernel and is a reference for the device's downstream drivers
and device tree; it is not a Nura kernel package.

## Port status

No device package, kernel recipe, board device tree, firmware package, or
boot-image integration is included here yet. Consequently, this repository
cannot currently build or install Nura on the R1.

The port needs, at minimum:

1. A Nura device package describing the R1's hardware, storage layout, and
   supported boot method.
2. A buildable kernel and R1 device tree, with a matching Nura kernel package.
3. A documented, reproducible way to provide any required firmware.
4. A boot-image/install flow that preserves the existing Android partitions
   until booting and recovery have been tested on-device.

The device-tree dump and vendor kernel are starting references, not ready-made
mainline support. A successful image build alone will not verify that it can
boot on an R1; validation requires testing boot, display, input, storage, and
recovery on the hardware.
