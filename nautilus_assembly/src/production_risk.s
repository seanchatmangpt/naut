// Ultimate fast risk validation - production ready
.section __TEXT,__text
.global _ultra_fast_risk_batch_simd
.global _ultra_fast_risk_single
.align 4

// Single risk check - optimized for hot path
// x0 = packed_order (price:32|qty:32), x1 = packed_limits
// Returns: x0 = 0 (valid) or 1 (invalid)
_ultra_fast_risk_single:
    // Unpack in parallel using bit manipulation
    ubfx x2, x0, #32, #32   // Extract price (bits 32-63)
    ubfx x3, x0, #0, #32    // Extract quantity (bits 0-31)
    
    ubfx x4, x1, #0, #16    // min_qty
    ubfx x5, x1, #16, #16   // max_qty  
    ubfx x6, x1, #32, #16   // min_price
    ubfx x7, x1, #48, #16   // max_price
    
    // Parallel comparisons
    cmp x2, x6              // price >= min_price
    ccmp x2, x7, #0, hs     // price <= max_price (if prev passed)
    ccmp x3, x4, #0, ls     // qty >= min_qty (if prev passed)
    ccmp x3, x5, #0, hs     // qty <= max_qty (if prev passed)
    
    cset x0, hi             // Set 1 if any failed
    ret

// Batch risk validation using NEON SIMD
// x0 = orders_ptr, x1 = results_ptr, x2 = count, x3 = limits
_ultra_fast_risk_batch_simd:
    // Extract limits once
    ubfx x4, x3, #0, #16    // min_qty
    ubfx x5, x3, #16, #16   // max_qty
    ubfx x6, x3, #32, #16   // min_price  
    ubfx x7, x3, #48, #16   // max_price
    
    // Broadcast to NEON registers
    dup v16.4s, w4          // min_qty in all lanes
    dup v17.4s, w5          // max_qty in all lanes
    dup v18.4s, w6          // min_price in all lanes
    dup v19.4s, w7          // max_price in all lanes
    
process_loop:
    // Process 8 orders at once (2 x 128-bit vectors)
    cmp x2, #8
    b.lt process_remainder
    
    // Load 8 orders (256 bits total)
    ld1 {v0.2d, v1.2d, v2.2d, v3.2d}, [x0], #64
    
    // Unpack prices and quantities
    // Even elements = quantities, odd = prices
    uzp1 v4.4s, v0.4s, v1.4s    // 4 quantities
    uzp2 v5.4s, v0.4s, v1.4s    // 4 prices
    uzp1 v6.4s, v2.4s, v3.4s    // 4 more quantities
    uzp2 v7.4s, v2.4s, v3.4s    // 4 more prices
    
    // SIMD comparisons for first 4
    cmhs v8.4s, v4.4s, v16.4s   // qty >= min_qty
    cmls v9.4s, v4.4s, v17.4s   // qty <= max_qty
    cmhs v10.4s, v5.4s, v18.4s  // price >= min_price
    cmls v11.4s, v5.4s, v19.4s  // price <= max_price
    
    // Combine results
    and v12.16b, v8.16b, v9.16b
    and v13.16b, v10.16b, v11.16b
    and v14.16b, v12.16b, v13.16b
    
    // SIMD comparisons for second 4
    cmhs v8.4s, v6.4s, v16.4s
    cmls v9.4s, v6.4s, v17.4s
    cmhs v10.4s, v7.4s, v18.4s
    cmls v11.4s, v7.4s, v19.4s
    
    and v12.16b, v8.16b, v9.16b
    and v13.16b, v10.16b, v11.16b
    and v15.16b, v12.16b, v13.16b
    
    // Pack results (valid = 0xFF, invalid = 0x00)
    // Convert to 0/1 format
    ushr v14.4s, v14.4s, #31    // Shift to get 0 or 1
    ushr v15.4s, v15.4s, #31
    
    // Store 8 results
    st1 {v14.4s}, [x1], #16
    st1 {v15.4s}, [x1], #16
    
    sub x2, x2, #8
    b process_loop
    
process_remainder:
    // Handle remaining orders one by one
    cbz x2, done
    
remainder_loop:
    ldr x8, [x0], #8        // Load order
    
    // Quick validation
    ubfx x9, x8, #32, #32   // price
    ubfx x10, x8, #0, #32   // quantity
    
    // Check bounds
    cmp x9, x6              // price >= min_price
    ccmp x9, x7, #0, hs     // price <= max_price
    ccmp x10, x4, #0, ls    // qty >= min_qty
    ccmp x10, x5, #0, hs    // qty <= max_qty
    
    cset w11, hi            // 1 if invalid
    str w11, [x1], #4       // Store result
    
    subs x2, x2, #1
    b.ne remainder_loop
    
done:
    ret
