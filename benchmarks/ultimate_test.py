#!/usr/bin/env python3
"""
Focused test for absolute best performance numbers
"""
import time
import numpy as np
import subprocess
import ctypes
import os

def create_optimized_assembly():
    """Create minimal, maximally optimized assembly"""
    asm_code = """
.section __TEXT,__text
.global _ultra_fast_loop
.align 4

// Ultra-minimal loop - just increment and compare
// Args: x0=iterations
// Returns: x0=result
_ultra_fast_loop:
    mov x1, #0              // counter = 0
    mov x2, #0              // sum = 0
    
loop:
    add x2, x2, x1          // sum += counter
    add x1, x1, #1          // counter++
    cmp x1, x0              // compare with iterations
    b.lt loop               // branch if less than
    
    mov x0, x2              // return sum
    ret

.global _simd_add_arrays
.align 4

// SIMD array addition - maximum vectorization
// Args: x0=dst, x1=src1, x2=src2, x3=count
_simd_add_arrays:
    mov x4, #4              // 4 floats per vector
    udiv x5, x3, x4         // number of vector operations
    
simd_loop:
    cbz x5, remaining
    
    ld1 {v0.4s}, [x1], #16  // load 4 floats from src1
    ld1 {v1.4s}, [x2], #16  // load 4 floats from src2
    fadd v2.4s, v0.4s, v1.4s // add vectors
    st1 {v2.4s}, [x0], #16  // store result
    
    sub x5, x5, #1
    b simd_loop
    
remaining:
    and x4, x3, #3          // remaining elements
    
scalar_loop:
    cbz x4, done
    
    ldr s0, [x1], #4
    ldr s1, [x2], #4
    fadd s2, s0, s1
    str s2, [x0], #4
    
    sub x4, x4, #1
    b scalar_loop
    
done:
    ret
"""
    
    with open("ultra_fast.s", "w") as f:
        f.write(asm_code)

def test_ultimate_performance():
    """Test ultimate performance limits"""
    print("🚀 ULTIMATE M3 MAX PERFORMANCE TEST")
    print("=" * 50)
    
    create_optimized_assembly()
    
    # Compile
    result = subprocess.run([
        "clang", "-c", "-arch", "arm64", "-O3", "-march=armv8.4-a+simd",
        "ultra_fast.s", "-o", "ultra_fast.o"
    ], capture_output=True, text=True)
    
    if result.returncode != 0:
        print(f"❌ Compilation failed: {result.stderr}")
        return
    
    # Create library
    result = subprocess.run([
        "clang", "-shared", "-arch", "arm64", "ultra_fast.o", 
        "-o", "libultra.dylib"
    ], capture_output=True, text=True)
    
    if result.returncode != 0:
        print(f"❌ Library creation failed: {result.stderr}")
        return
    
    # Load and test
    lib = ctypes.CDLL("./libultra.dylib")
    
    # Test 1: Ultra-fast loop
    lib.ultra_fast_loop.argtypes = [ctypes.c_uint64]
    lib.ultra_fast_loop.restype = ctypes.c_uint64
    
    print("\n⚡ Ultra-Fast Assembly Loop:")
    iterations = 1_000_000_000
    
    start_time = time.perf_counter_ns()
    result = lib.ultra_fast_loop(iterations)
    end_time = time.perf_counter_ns()
    
    total_time = end_time - start_time
    per_iter_ns = total_time / iterations
    
    print(f"  Iterations: {iterations:,}")
    print(f"  Total time: {total_time/1e9:.3f}s")
    print(f"  Per iteration: {per_iter_ns:.3f}ns")
    print(f"  Throughput: {1e9/per_iter_ns:,.0f} ops/sec")
    print(f"  CPU cycles: {per_iter_ns * 4.05:.1f} (at 4.05GHz)")
    
    # Test 2: SIMD array operations
    lib.simd_add_arrays.argtypes = [
        ctypes.POINTER(ctypes.c_float),
        ctypes.POINTER(ctypes.c_float), 
        ctypes.POINTER(ctypes.c_float),
        ctypes.c_uint64
    ]
    
    print("\n🧮 Ultra-Fast SIMD Operations:")
    size = 10_000_000
    
    src1 = np.random.uniform(0, 100, size).astype(np.float32)
    src2 = np.random.uniform(0, 100, size).astype(np.float32)
    dst = np.zeros(size, dtype=np.float32)
    
    src1_ptr = src1.ctypes.data_as(ctypes.POINTER(ctypes.c_float))
    src2_ptr = src2.ctypes.data_as(ctypes.POINTER(ctypes.c_float))
    dst_ptr = dst.ctypes.data_as(ctypes.POINTER(ctypes.c_float))
    
    # Warm up
    lib.simd_add_arrays(dst_ptr, src1_ptr, src2_ptr, size)
    
    iterations = 1000
    start_time = time.perf_counter_ns()
    
    for _ in range(iterations):
        lib.simd_add_arrays(dst_ptr, src1_ptr, src2_ptr, size)
    
    end_time = time.perf_counter_ns()
    total_time = end_time - start_time
    per_op_ns = total_time / iterations
    
    print(f"  Array size: {size:,}")
    print(f"  Operations: {iterations:,}")
    print(f"  Per operation: {per_op_ns/1000:.2f}μs")
    print(f"  Throughput: {size*1e9/per_op_ns:,.0f} elements/sec")
    print(f"  SIMD efficiency: {size*4*1e9/per_op_ns/1e9:.1f} GB/s")
    
    # Cleanup
    os.remove("ultra_fast.s")
    os.remove("ultra_fast.o") 
    os.remove("libultra.dylib")
    
    print(f"\n🏆 ABSOLUTE BEST RESULTS:")
    print(f"  Fastest loop: {per_iter_ns:.3f}ns per iteration")
    print(f"  SIMD throughput: {size*1e9/per_op_ns:,.0f} elements/sec")
    print(f"  This is REAL assembly performance on your M3 Max!")
    
    return per_iter_ns, size*1e9/per_op_ns

if __name__ == "__main__":
    test_ultimate_performance()
