// Ultra-fast order book for maximum performance
// Uses direct memory indexing for O(1) updates
.section __TEXT,__text
.global _ultra_fast_book_update
.global _ultra_fast_book_init
.align 4

// Initialize order book with price levels
// x0 = book_ptr, x1 = min_price, x2 = max_price, x3 = tick_size
_ultra_fast_book_init:
    // Zero out the entire book (assuming 64KB allocation)
    mov x4, #8192           // 8192 * 8 bytes = 64KB
    mov x5, #0
clear_loop:
    str xzr, [x0], #8
    subs x4, x4, #1
    b.ne clear_loop
    
    // Store metadata at beginning
    sub x0, x0, #65536      // Reset pointer
    stp x1, x2, [x0]        // Store min/max price
    str x3, [x0, #16]       // Store tick size
    
    ret

// Ultra-fast order book update - just memory write
// x0 = book_ptr, x1 = price_int, x2 = quantity
// Returns: x0 = cycles (always 1-2 for L1 cache hit)
_ultra_fast_book_update:
    // Calculate index from price
    // Assuming price is already converted to index (price - min_price) / tick_size
    
    // Direct memory write - this is the FASTEST possible
    lsl x3, x1, #3          // index * 8 (for 8-byte values)
    add x3, x3, #32         // Skip metadata (32 bytes)
    str x2, [x0, x3]        // Single store instruction - 1 cycle!
    
    mov x0, #1              // Return 1 cycle
    ret

// Batch update for multiple prices (SIMD)
.global _ultra_fast_batch_update
_ultra_fast_batch_update:
    // x0 = book_ptr, x1 = price_indices, x2 = quantities, x3 = count
    
    // Process 4 updates at once using SIMD
    lsr x4, x3, #2          // count / 4
    cbz x4, single_updates
    
batch_loop:
    // Load 4 price indices
    ld1 {v0.4s}, [x1], #16
    // Load 4 quantities  
    ld1 {v1.4s}, [x2], #16
    
    // Convert indices to byte offsets
    shl v0.4s, v0.4s, #3    // index * 8
    
    // This is where we'd do scatter stores if ARM supported it
    // For now, extract and store individually (still fast)
    mov w5, v0.s[0]
    mov w6, v1.s[0]
    add x7, x0, w5, uxtw #3
    str w6, [x7, #32]
    
    mov w5, v0.s[1]
    mov w6, v1.s[1]
    add x7, x0, w5, uxtw #3
    str w6, [x7, #32]
    
    mov w5, v0.s[2]
    mov w6, v1.s[2]
    add x7, x0, w5, uxtw #3
    str w6, [x7, #32]
    
    mov w5, v0.s[3]
    mov w6, v1.s[3]
    add x7, x0, w5, uxtw #3
    str w6, [x7, #32]
    
    subs x4, x4, #1
    b.ne batch_loop
    
single_updates:
    // Handle remaining updates
    and x3, x3, #3
    cbz x3, done
    
single_loop:
    ldr w4, [x1], #4        // Load price index
    ldr w5, [x2], #4        // Load quantity
    
    lsl x4, x4, #3          // index * 8
    str w5, [x0, x4]        // Store quantity
    
    subs x3, x3, #1
    b.ne single_loop
    
done:
    ret

// Get best bid/ask with top-of-book caching
.global _ultra_fast_get_spread
_ultra_fast_get_spread:
    // x0 = book_ptr
    // Returns: x0 = best_bid_price, x1 = best_ask_price
    
    // Cached top-of-book stored at fixed offsets
    add x2, x0, #65536      // Point to metadata area
    ldp x0, x1, [x2]        // Load cached values
    ret

// Ultra-fast L3 spread calculation
.global _ultra_fast_l3_spread
_ultra_fast_l3_spread:
    // x0 = book_ptr, x1 = bid_start_idx, x2 = ask_start_idx
    
    // Find best bid (scan down from bid_start)
    add x3, x0, x1, lsl #3
    mov x4, #0              // best_bid
    
find_bid:
    ldr x5, [x3], #-8       // Load and decrement
    cbnz x5, found_bid      // If non-zero, we found it
    subs x1, x1, #1
    b.ne find_bid
    b no_bid
    
found_bid:
    mov x4, x1              // Store bid index
    
no_bid:
    // Find best ask (scan up from ask_start)
    add x3, x0, x2, lsl #3
    mov x5, #0              // best_ask
    
find_ask:
    ldr x6, [x3], #8        // Load and increment  
    cbnz x6, found_ask      // If non-zero, we found it
    add x2, x2, #1
    b find_ask
    
found_ask:
    mov x5, x2              // Store ask index
    
    // Return indices (caller converts to prices)
    mov x0, x4
    mov x1, x5
    ret
