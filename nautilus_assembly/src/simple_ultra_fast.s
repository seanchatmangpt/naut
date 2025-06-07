// Simplest possible ultra-fast order book
// Direct memory writes only - no fancy features
.section __TEXT,__text
.global _ultra_fast_update
.global _ultra_fast_batch
.align 4

// Single update - just a store instruction
// x0 = base_ptr, x1 = offset, x2 = value
// This is literally the fastest possible: 1 instruction
_ultra_fast_update:
    str x2, [x0, x1, lsl #3]    // Single store - 1 cycle!
    ret

// Batch updates using SIMD
// x0 = base_ptr, x1 = offsets_ptr, x2 = values_ptr, x3 = count
_ultra_fast_batch:
    // Process 2 at a time (using paired loads/stores)
    lsr x4, x3, #1              // count / 2
    cbz x4, single_updates
    
paired_loop:
    ldp x5, x6, [x1], #16       // Load 2 offsets
    ldp x7, x8, [x2], #16       // Load 2 values
    
    // Store to calculated addresses
    str x7, [x0, x5, lsl #3]    // Store first
    str x8, [x0, x6, lsl #3]    // Store second
    
    subs x4, x4, #1
    b.ne paired_loop
    
single_updates:
    // Handle odd count
    and x3, x3, #1
    cbz x3, done
    
    ldr x5, [x1]                // Load offset
    ldr x6, [x2]                // Load value
    str x6, [x0, x5, lsl #3]    // Store
    
done:
    ret

// Ultra-fast spread calculation
// x0 = book_ptr, x1 = bid_offset, x2 = ask_offset
// Returns: x0 = spread
_ultra_fast_spread:
    ldr x3, [x0, x1, lsl #3]    // Load bid
    ldr x4, [x0, x2, lsl #3]    // Load ask
    sub x0, x4, x3              // Calculate spread
    ret
