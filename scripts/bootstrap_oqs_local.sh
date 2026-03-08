#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
REPO_ROOT=$(CDPATH= cd -- "$SCRIPT_DIR/.." && pwd)
VENDOR_DIR="$REPO_ROOT/.vendor"

LIBOQS_REF="${LIBOQS_REF:-0.10.0}"
LIBOQS_PY_REF="${LIBOQS_PY_REF:-0.10.0}"

LIBOQS_SRC_DIR="$VENDOR_DIR/liboqs-src"
LIBOQS_BUILD_DIR="$LIBOQS_SRC_DIR/build"
LIBOQS_PY_SRC_DIR="$VENDOR_DIR/liboqs-python-src"

export OQS_INSTALL_PATH=/home/rebel/_oqs
if [ -d "$OQS_INSTALL_PATH/lib64" ]; then
  export LD_LIBRARY_PATH="$OQS_INSTALL_PATH/lib64:${LD_LIBRARY_PATH:-}"
else
  export LD_LIBRARY_PATH="$OQS_INSTALL_PATH/lib:${LD_LIBRARY_PATH:-}"
fi

if [ -d "$OQS_INSTALL_PATH/lib64/pkgconfig" ]; then
  export PKG_CONFIG_PATH="$OQS_INSTALL_PATH/lib64/pkgconfig${PKG_CONFIG_PATH:+:$PKG_CONFIG_PATH}"
else
  export PKG_CONFIG_PATH="$OQS_INSTALL_PATH/lib/pkgconfig${PKG_CONFIG_PATH:+:$PKG_CONFIG_PATH}"
fi

mkdir -p "$VENDOR_DIR"

if [ ! -d "$LIBOQS_SRC_DIR/.git" ]; then
  echo "Cloning liboqs ($LIBOQS_REF) ..."
  git clone --depth 1 --branch "$LIBOQS_REF" https://github.com/open-quantum-safe/liboqs.git "$LIBOQS_SRC_DIR"
else
  echo "Using existing liboqs clone: $LIBOQS_SRC_DIR"
fi

if [ ! -d "$LIBOQS_PY_SRC_DIR/.git" ]; then
  echo "Cloning liboqs-python ($LIBOQS_PY_REF) ..."
  git clone --depth 1 --branch "$LIBOQS_PY_REF" https://github.com/open-quantum-safe/liboqs-python.git "$LIBOQS_PY_SRC_DIR"
else
  echo "Using existing liboqs-python clone: $LIBOQS_PY_SRC_DIR"
fi

mkdir -p "$OQS_INSTALL_PATH"

CMAKE_ARGS=(
  -S "$LIBOQS_SRC_DIR"
  -B "$LIBOQS_BUILD_DIR"
  -DBUILD_SHARED_LIBS=ON
  -DOQS_BUILD_ONLY_LIB=ON
  -DCMAKE_INSTALL_PREFIX="$OQS_INSTALL_PATH"
)

if command -v ninja >/dev/null 2>&1; then
  CMAKE_ARGS+=(-GNinja)
fi

echo "Configuring liboqs ..."
cmake "${CMAKE_ARGS[@]}"

echo "Building liboqs ..."
cmake --build "$LIBOQS_BUILD_DIR" --parallel

echo "Installing liboqs to $OQS_INSTALL_PATH ..."
cmake --install "$LIBOQS_BUILD_DIR"

echo "OQS_INSTALL_PATH=$OQS_INSTALL_PATH"
echo "LD_LIBRARY_PATH=$LD_LIBRARY_PATH"
echo "Installing liboqs-python into the active environment ..."
python -m pip install --no-build-isolation --no-deps --upgrade "$LIBOQS_PY_SRC_DIR"

PYTHON_EXE=$(command -v python)
PIP_EXE=$(command -v pip || true)
OQS_MODULE_PATH=$(python -c "import oqs; print(oqs.__file__)")

echo "Bootstrap succeeded."
echo " - python: $PYTHON_EXE"
echo " - pip: ${PIP_EXE:-<not found on PATH>}"
echo " - OQS_INSTALL_PATH: $OQS_INSTALL_PATH"
echo " - liboqs source: $LIBOQS_SRC_DIR"
echo " - liboqs-python source: $LIBOQS_PY_SRC_DIR"
echo " - oqs module: $OQS_MODULE_PATH"
