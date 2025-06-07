cmake_minimum_required(VERSION 3.20)
project(nautilus_assembly_engine)

# Set compilers to Clang for best ARM64 optimization
set(CMAKE_C_COMPILER clang)
set(CMAKE_CXX_COMPILER clang++)
set(CMAKE_ASM_COMPILER clang)

# Enable assembly language
enable_language(ASM)

# M3 Max specific optimizations
set(ARM64_FLAGS "-march=armv8.4-a+simd -mcpu=apple-m1 -mtune=apple-m1")
set(CMAKE_C_FLAGS "${CMAKE_C_FLAGS} ${ARM64_FLAGS}")
set(CMAKE_CXX_FLAGS "${CMAKE_CXX_FLAGS} ${ARM64_FLAGS}")
set(CMAKE_ASM_FLAGS "${CMAKE_ASM_FLAGS} ${ARM64_FLAGS}")

# Release build optimizations
set(CMAKE_C_FLAGS_RELEASE "-O3 -DNDEBUG -flto -ffast-math -funroll-loops")
set(CMAKE_CXX_FLAGS_RELEASE "-O3 -DNDEBUG -flto -ffast-math -funroll-loops")

# Debug build with assembly debugging
set(CMAKE_C_FLAGS_DEBUG "-O0 -g -DDEBUG")
set(CMAKE_CXX_FLAGS_DEBUG "-O0 -g -DDEBUG")

# Include directories
include_directories(
    ${CMAKE_CURRENT_SOURCE_DIR}/nautilus_assembly/include
    /opt/homebrew/include
)

# Assembly source files
set(ASSEMBLY_SOURCES
    nautilus_assembly/src/order_book.s
    nautilus_assembly/src/market_data.s
    nautilus_assembly/src/signals.s
    nautilus_assembly/src/risk_engine.s
)

# Create assembly library
add_library(nautilus_assembly_core STATIC ${ASSEMBLY_SOURCES})

# Set assembly-specific properties
set_target_properties(nautilus_assembly_core PROPERTIES
    LINKER_LANGUAGE C
    POSITION_INDEPENDENT_CODE ON
)

# Install targets
install(TARGETS nautilus_assembly_core
    ARCHIVE DESTINATION lib
    LIBRARY DESTINATION lib
)

install(FILES nautilus_assembly/include/assembly_engine.h
    DESTINATION include
)

# Testing (optional)
option(BUILD_TESTS "Build unit tests" OFF)
if(BUILD_TESTS)
    enable_testing()
    add_subdirectory(tests)
endif()

# Benchmarking (optional)
option(BUILD_BENCHMARKS "Build performance benchmarks" ON)
if(BUILD_BENCHMARKS)
    add_subdirectory(benchmarks)
endif()
