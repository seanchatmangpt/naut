// test_assembly.s
// Simple test to verify ARM64 assembly syntax
.section __TEXT,__text
.global _test_add
.align 2

// Simple function: add two integers
// x0 = a, x1 = b, returns x0 = a + b
_test_add:
    add x0, x0, x1
    ret

.global _test_float_add
.align 2

// Add two floats
// s0 = a, s1 = b, returns s0 = a + b
_test_float_add:
    fadd s0, s0, s1
    ret

.global _test_simd_add
.align 2

// SIMD add of 4 floats
// v0 = vector a, v1 = vector b, returns v0 = a + b
_test_simd_add:
    fadd v0.4s, v0.4s, v1.4s
    ret
