# setup.py
"""
Setup script for NautilusTrader ARM64 Assembly Engine
Optimized for Apple M3 Max performance
"""
from setuptools import setup, Extension
from Cython.Build import cythonize
import numpy as np
import os

# ARM64 assembly compilation flags for M3 Max
assembly_flags = [
    "-march=armv8.4-a+simd",
    "-mcpu=apple-m1",  # Close enough for M3 Max
    "-O3",
    "-flto",
    "-ffast-math",
    "-funroll-loops",
    "-fomit-frame-pointer",
    "-DNDEBUG",
]

# Linker flags
linker_flags = [
    "-flto",
    "-Wl,-dead_strip",  # Remove unused code on macOS
]

# Include directories
include_dirs = [
    np.get_include(),
    "nautilus_assembly/include",
    "/opt/homebrew/include",  # Common Homebrew path for M3 Max
]

# Source files
assembly_sources = [
    "nautilus_assembly/src/order_book.s",
    "nautilus_assembly/src/market_data.s",
    "nautilus_assembly/src/signals.s",
    "nautilus_assembly/src/risk_engine.s",
]

# Main extension module
extensions = [
    Extension(
        "nautilus_assembly",
        sources=[
            "nautilus_assembly/nautilus_assembly.pyx",
        ] + assembly_sources,
        include_dirs=include_dirs,
        extra_compile_args=assembly_flags,
        extra_link_args=linker_flags,
        language="c++",
        define_macros=[
            ("NPY_NO_DEPRECATED_API", "NPY_1_7_API_VERSION"),
            ("ARM64_ASSEMBLY_ENABLED", "1"),
        ],
    )
]

# Cython compiler directives for maximum performance
compiler_directives = {
    "boundscheck": False,
    "wraparound": False,
    "cdivision": True,
    "language_level": 3,
    "embedsignature": True,
    "optimize.use_switch": True,
    "optimize.unpack_method_calls": True,
}

setup(
    name="nautilus-assembly-engine",
    version="1.0.0",
    description="High-performance ARM64 assembly engine for NautilusTrader",
    author="SAC",
    python_requires=">=3.9",
    ext_modules=cythonize(
        extensions, 
        compiler_directives=compiler_directives,
        annotate=True,  # Generate HTML annotation files
    ),
    install_requires=[
        "numpy>=1.21.0",
        "cython>=0.29.0",
        "nautilus_trader>=1.180.0",
    ],
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Financial and Insurance Industry",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Assembly",
        "Topic :: Office/Business :: Financial :: Investment",
        "Topic :: Scientific/Engineering :: Mathematics",
    ],
    zip_safe=False,
)
