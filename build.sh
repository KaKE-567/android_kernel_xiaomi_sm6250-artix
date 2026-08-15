#!/usr/bin/env bash
#
# ArtixV4 Kernel Build Script
# Target: Xiaomi SM6250 (Atoll) / cust_defconfig
# Toolchain: Proton Clang 13
#

set -e

KERNEL_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
OUT_DIR="${KERNEL_DIR}/out"
DEFCONFIG="cust_defconfig"
TOOLCHAIN_DIR="/home/codespace/proton-clang"

export PATH="${TOOLCHAIN_DIR}/bin:/usr/bin:/bin:$PATH"
export ARCH="arm64"
export SUBARCH="arm64"
export CC="clang"
export HOSTCC="gcc -B/usr/bin/"
export HOSTCXX="g++ -B/usr/bin/"
export CROSS_COMPILE="${TOOLCHAIN_DIR}/bin/aarch64-linux-gnu-"
export CROSS_COMPILE_ARM32="${TOOLCHAIN_DIR}/bin/arm-linux-gnueabi-"
export CROSS_COMPILE_COMPAT="${TOOLCHAIN_DIR}/bin/arm-linux-gnueabi-"
export CLANG_TRIPLE="aarch64-linux-gnu-"
export LD="ld.lld"
export AR="llvm-ar"
export NM="llvm-nm"
export OBJCOPY="llvm-objcopy"
export OBJDUMP="llvm-objdump"
export STRIP="llvm-strip"
export KBUILD_BUILD_USER="KaKe"
export KBUILD_BUILD_HOST="Artix"

JOBS="$(nproc --all)"

echo "============================================="
echo "  Building ArtixV4 Gaming Kernel"
echo "  Target SoC: Xiaomi SM6250 (Atoll)"
echo "  Defconfig : ${DEFCONFIG}"
echo "  Toolchain : Proton Clang 13 ($(clang --version | head -n 1 | awk '{print $1,$2,$3,$4}'))"
echo "  Threads   : ${JOBS}"
echo "============================================="

START_TIME=$(date +%s)

mkdir -p "${OUT_DIR}"

echo "[1/2] Generating defconfig (${DEFCONFIG})..."
make O="${OUT_DIR}" ARCH="${ARCH}" CC="${CC}" HOSTCC="${HOSTCC}" HOSTCXX="${HOSTCXX}" \
     CROSS_COMPILE="${CROSS_COMPILE}" CROSS_COMPILE_ARM32="${CROSS_COMPILE_ARM32}" \
     LD="${LD}" AR="${AR}" NM="${NM}" OBJCOPY="${OBJCOPY}" OBJDUMP="${OBJDUMP}" STRIP="${STRIP}" \
     "${DEFCONFIG}"

echo "[2/2] Compiling Kernel (Image.gz-dtb and dtbs)..."
make O="${OUT_DIR}" ARCH="${ARCH}" CC="${CC}" HOSTCC="${HOSTCC}" HOSTCXX="${HOSTCXX}" \
     CROSS_COMPILE="${CROSS_COMPILE}" CROSS_COMPILE_ARM32="${CROSS_COMPILE_ARM32}" \
     LD="${LD}" AR="${AR}" NM="${NM}" OBJCOPY="${OBJCOPY}" OBJDUMP="${OBJDUMP}" STRIP="${STRIP}" \
     -j"${JOBS}" Image.gz-dtb dtbs

# Generate dtbo.img from compiled overlay dtbo files
if ls "${OUT_DIR}"/arch/arm64/boot/dts/qcom/*overlay.dtbo 1> /dev/null 2>&1; then
    echo "Creating dtbo.img..."
    python3 "${KERNEL_DIR}/scripts/mkdtboimg.py" create "${OUT_DIR}/arch/arm64/boot/dtbo.img" \
            "${OUT_DIR}"/arch/arm64/boot/dts/qcom/*overlay.dtbo
fi

END_TIME=$(date +%s)
DURATION=$((END_TIME - START_TIME))

if [ -f "${OUT_DIR}/arch/arm64/boot/Image.gz-dtb" ]; then
    echo "============================================="
    echo "  BUILD SUCCESSFUL in $((DURATION / 60))m $((DURATION % 60))s"
    echo "  Kernel Image: ${OUT_DIR}/arch/arm64/boot/Image.gz-dtb"
    if [ -f "${OUT_DIR}/arch/arm64/boot/dtbo.img" ]; then
        echo "  DTBO Image  : ${OUT_DIR}/arch/arm64/boot/dtbo.img"
    fi
    echo "============================================="
else
    echo "============================================="
    echo "  BUILD FAILED: Kernel image not found."
    echo "============================================="
    exit 1
fi
