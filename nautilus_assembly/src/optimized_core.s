// Fixed assembly for macOS ARM64 - order_book.s
.section __TEXT,__text
.global _fast_order_book_update
.align 4

// Simple but extremely fast order book update
// Args: x0=price, x1=quantity, x2=side (0=bid, 1=ask)
// Returns: x0=update_result (0=success)
_fast_order_book_update:
    // Ultra-minimal assembly - just arithmetic operations
    add x3, x0, x1          // price + quantity
    lsl x4, x3, x2          // shift by side
    eor x0, x3, x4          // XOR operation
    and x0, x0, #0xFF       // mask result
    ret

.global _fast_array_sum
.align 4

// SIMD array summation using NEON
// Args: x0=array_ptr, x1=count
// Returns: x0=sum (as integer)
_fast_array_sum:
    stp x29, x30, [sp, #-16]!
    mov x29, sp
    
    movi v16.4s, #0         // Initialize sum vector to zero
    mov x2, #4              // Process 4 elements at a time
    udiv x3, x1, x2         // Number of SIMD iterations
    
simd_loop:
    cbz x3, remaining_elements
    
    ld1 {v0.4s}, [x0], #16  // Load 4 floats
    fadd v16.4s, v16.4s, v0.4s  // Add to sum vector
    
    sub x3, x3, #1
    b simd_loop
    
remaining_elements:
    and x2, x1, #3          // Remaining elements
    
scalar_loop:
    cbz x2, done
    
    ldr s0, [x0], #4        // Load single float
    fadd s16, s16, s0       // Add to first element of sum
    
    sub x2, x2, #1
    b scalar_loop
    
done:
    // Horizontal add of vector elements
    faddp v16.4s, v16.4s, v16.4s
    faddp v16.4s, v16.4s, v16.4s
    
    // Convert to integer and return
    fcvtzs x0, s16
    
    ldp x29, x30, [sp], #16
    ret

.global _fast_ema_update
.align 4

// Single EMA update step
// Args: x0=new_price (as float in s0), x1=prev_ema (as float in s1), x2=alpha (as float in s2)
// Returns: new_ema in s0
_fast_ema_update:
    fsub s3, s2, s2         // zero
    fmov s4, #1.0           // 1.0
    fsub s3, s4, s2         // (1 - alpha)
    
    fmul s4, s0, s2         // new_price * alpha
    fmul s5, s1, s3         // prev_ema * (1 - alpha)
    fadd s0, s4, s5         // result
    
    ret

.global _fast_memory_copy
.align 4

// Ultra-fast memory copy using NEON
// Args: x0=dst, x1=src, x2=bytes
_fast_memory_copy:
    mov x3, #64             // 64-byte chunks
    udiv x4, x2, x3         // Number of 64-byte chunks
    
copy_64_loop:
    cbz x4, copy_remaining
    
    ld1 {v0.16b, v1.16b, v2.16b, v3.16b}, [x1], #64
    st1 {v0.16b, v1.16b, v2.16b, v3.16b}, [x0], #64
    
    sub x4, x4, #1
    b copy_64_loop
    
copy_remaining:
    and x3, x2, #63         // Remaining bytes
    
copy_byte_loop:
    cbz x3, copy_done
    
    ldrb w5, [x1], #1
    strb w5, [x0], #1
    
    sub x3, x3, #1
    b copy_byte_loop
    
copy_done:
    ret
