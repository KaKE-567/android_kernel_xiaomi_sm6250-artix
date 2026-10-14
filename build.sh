#!/bin/bash
set -e
cd /workspaces/android_kernel_xiaomi_sm6250-artix

export ARCH=arm64
export SUBARCH=arm64
export CROSS_COMPILE=aarch64-linux-gnu-
export CROSS_COMPILE_ARM32=arm-linux-gnueabi-
export CC=/home/codespace/proton-clang/bin/clang
export CLANG_TRIPLE=aarch64-linux-gnu-
export HOSTCC=gcc
export HOSTLD=/usr/bin/ld
export KBUILD_BUILD_USER=android-build
export KBUILD_BUILD_HOST=google

echo "=== Generating cust_defconfig ==="
make O=out ARCH=arm64 HOSTCC=gcc HOSTLD=/usr/bin/ld cust_defconfig

echo "=== Building Image.gz-dtb ==="
make -j$(nproc --all) O=out \
    ARCH=arm64 \
    CC=/home/codespace/proton-clang/bin/clang \
    CLANG_TRIPLE=aarch64-linux-gnu- \
    CROSS_COMPILE=aarch64-linux-gnu- \
    CROSS_COMPILE_ARM32=arm-linux-gnueabi- \
    HOSTCC=gcc \
    HOSTLD=/usr/bin/ld \
    Image.gz-dtb

echo "=== Build Complete ==="
ls -lh out/arch/arm64/boot/Image.gz-dtb
