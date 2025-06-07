// nautilus_assembly/src/order_book.s
// Ultra-fast order book processing for M3 Max ARM64
.section __DATA,__data
.align 6                    // 64-byte cache line alignment

// Order book level structure (16 bytes, cache-friendly)
.struct 0
price_field:     .space 8   // f64 price
quantity_field:  .space 8   // f64 quantity
.end

// L1/L2/L3 order book structure  
.struct 0
bids_array:      .space 8   // Pointer to bids
asks_array:      .space 8   // Pointer to asks
bid_count:       .space 4   // Current bid levels
ask_count:       .space 4   // Current ask levels
bid_capacity:    .space 4   // Max bid levels
ask_capacity:    .space 4   // Max ask levels
instrument_id:   .space 8   // Nautilus instrument ID
sequence:        .space 8   // Sequence number
timestamp_ns:    .space 8   // Nautilus timestamp
.end

.section __TEXT,__text
.global _nautilus_update_l2_level
.align 4

// Args: x0=order_book*, x1=side(0=bid,1=ask), x2=price_raw, x3=qty_raw, x4=action
// Returns: x0=update_flags (bit 0=book_changed, bit 1=top_changed)
_nautilus_update_l2_level:
    stp x29, x30, [sp, #-32]!
    stp x19, x20, [sp, #16]
    mov x29, sp
    
    // Load book metadata
    ldr x5, [x0, #bids_array]    // bids pointer
    ldr x6, [x0, #asks_array]    // asks pointer
    ldr w7, [x0, #bid_count]     // current bid count
    ldr w8, [x0, #ask_count]     // current ask count
    
    // Select working array based on side
    cmp x1, #0
    csel x9, x5, x6, eq          // working_array = side ? asks : bids
    csel w10, w7, w8, eq         // working_count = side ? ask_count : bid_count
    
    // Binary search for price level
    mov x11, #0                  // left = 0
    mov x12, x10                 // right = count
    mov x19, #0                  // found_index
    mov x20, #0                  // update_flags
    
binary_search:
    cmp x11, x12
    b.ge not_found
    
    add x13, x11, x12
    lsr x13, x13, #1             // mid = (left + right) / 2
    
    lsl x14, x13, #4             // offset = mid * 16
    ldr x15, [x9, x14]           // level_price = levels[mid].price
    
    cmp x2, x15                  // compare search_price with level_price
    b.eq found_exact
    
    // For bids: descending order, for asks: ascending order
    cmp x1, #0                   // Check if bids (descending)
    b.eq bid_search
    
ask_search:
    cmp x2, x15                  // price < level_price
    b.lt search_left_ask
    add x11, x13, #1             // left = mid + 1
    b binary_search
    
search_left_ask:
    mov x12, x13                 // right = mid
    b binary_search
    
bid_search:
    cmp x2, x15                  // price > level_price (bids descending)
    b.gt search_left_bid
    add x11, x13, #1             // left = mid + 1  
    b binary_search
    
search_left_bid:
    mov x12, x13                 // right = mid
    b binary_search
    
found_exact:
    mov x19, x13                 // found_index = mid
    
    // Check if this is top of book
    cbz x13, top_of_book_update
    orr x20, x20, #1             // Set book_changed flag
    b update_existing_level
    
top_of_book_update:
    orr x20, x20, #3             // Set both book_changed and top_changed
    
update_existing_level:
    lsl x14, x19, #4             // offset = index * 16
    
    // Check action: 0=update, 1=delete
    cmp x4, #1
    b.eq delete_level
    
    // Update quantity
    add x15, x9, x14
    str x3, [x15, #8]            // Store new quantity
    b update_counts
    
delete_level:
    // Shift array left to remove level
    add x13, x19, #1             // start_index = found_index + 1
    
shift_loop:
    cmp x13, x10                 // while start_index < count
    b.ge shift_done
    
    lsl x14, x13, #4             // source_offset = start_index * 16
    sub x15, x14, #16            // dest_offset = (start_index - 1) * 16
    
    // Copy 16-byte level
    ldp x16, x17, [x9, x14]
    stp x16, x17, [x9, x15]
    
    add x13, x13, #1
    b shift_loop
    
shift_done:
    sub x10, x10, #1             // Decrement count
    b update_counts
    
not_found:
    // Insert new level at position x11
    cbz x3, skip_insert          // Skip if quantity is 0
    
    // Shift array right to make space
    mov x13, x10                 // start from end
    
insert_shift_loop:
    cmp x13, x11                 // while index > insert_position
    b.le insert_new
    
    sub x14, x13, #1
    lsl x15, x14, #4             // source_offset
    lsl x16, x13, #4             // dest_offset
    
    ldp x17, x18, [x9, x15]
    stp x17, x18, [x9, x16]
    
    sub x13, x13, #1
    b insert_shift_loop
    
insert_new:
    lsl x14, x11, #4             // insert_offset = position * 16
    add x15, x9, x14
    str x2, [x15]                // Store price
    str x3, [x15, #8]            // Store quantity
    
    add x10, x10, #1             // Increment count
    orr x20, x20, #1             // Set book_changed flag
    
    // Check if inserted at top
    cbz x11, inserted_at_top
    b update_counts
    
inserted_at_top:
    orr x20, x20, #2             // Set top_changed flag
    
update_counts:
    // Update counts in book structure
    cmp x1, #0
    b.eq update_bid_count
    str w10, [x0, #ask_count]
    b update_sequence
    
update_bid_count:
    str w10, [x0, #bid_count]
    
update_sequence:
    ldr x13, [x0, #sequence]
    add x13, x13, #1
    str x13, [x0, #sequence]
    
skip_insert:
    mov x0, x20                  // Return update flags
    
cleanup:
    ldp x19, x20, [sp, #16]
    ldp x29, x30, [sp], #32
    ret

.global _nautilus_get_best_bid_ask
.align 4

// Args: x0=order_book*
// Returns: x0=best_bid_price, x1=best_ask_price
_nautilus_get_best_bid_ask:
    stp x29, x30, [sp, #-16]!
    mov x29, sp
    
    // Load bid and ask arrays
    ldr x1, [x0, #bids_array]
    ldr x2, [x0, #asks_array]
    ldr w3, [x0, #bid_count]
    ldr w4, [x0, #ask_count]
    
    // Get best bid (first element in bids array)
    cbz w3, no_bids
    ldr x5, [x1]                 // best_bid_price
    b check_asks
    
no_bids:
    mov x5, #0                   // No bid available
    
check_asks:
    // Get best ask (first element in asks array)
    cbz w4, no_asks
    ldr x6, [x2]                 // best_ask_price
    b return_prices
    
no_asks:
    mov x6, #0                   // No ask available
    
return_prices:
    mov x0, x5                   // Return best bid
    mov x1, x6                   // Return best ask
    
    ldp x29, x30, [sp], #16
    ret
