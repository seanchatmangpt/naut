# Fixed Cython bindings
from libc.stdint cimport uint64_t, int32_t, uintptr_t
from libc.stdlib cimport malloc, free
import numpy as np
cimport numpy as cnp

cdef extern from "optimized_core.h":
    uint64_t fast_order_book_update(uint64_t price, uint64_t quantity, uint64_t side) nogil
    uint64_t fast_array_sum(float* array, uint64_t count) nogil
    void fast_memory_copy(void* dst, void* src, uint64_t bytes) nogil
    float fast_ema_update(float new_price, float prev_ema, float alpha) nogil

cdef class AssemblyEngine:
    """Real ARM64 assembly engine"""
    
    def __init__(self):
        pass
    
    def order_book_update(self, double price, double quantity, int side):
        """Ultra-fast order book update using assembly"""
        cdef uint64_t price_int = <uint64_t>(price * 1000000)
        cdef uint64_t qty_int = <uint64_t>(quantity * 1000000)
        cdef uint64_t result
        
        with nogil:
            result = fast_order_book_update(price_int, qty_int, side)
        
        return result
    
    def array_sum(self, cnp.ndarray[float, ndim=1] array):
        """SIMD array summation"""
        cdef uint64_t count = array.shape[0]
        cdef uint64_t result
        
        with nogil:
            result = fast_array_sum(&array[0], count)
        
        return result
    
    def ema_batch(self, cnp.ndarray[float, ndim=1] prices, float alpha):
        """Batch EMA calculation using assembly"""
        cdef uint64_t count = prices.shape[0]
        cdef cnp.ndarray[float, ndim=1] result = np.zeros(count, dtype=np.float32)
        cdef float ema_val = prices[0]
        cdef int i
        
        result[0] = ema_val
        
        for i in range(1, count):
            with nogil:
                ema_val = fast_ema_update(prices[i], ema_val, alpha)
            result[i] = ema_val
        
        return result
    
    def memory_copy_test(self, cnp.ndarray[uint8_t, ndim=1] src):
        """Test assembly memory copy performance"""
        cdef uint64_t size = src.shape[0]
        cdef cnp.ndarray[uint8_t, ndim=1] dst = np.zeros(size, dtype=np.uint8)
        
        with nogil:
            fast_memory_copy(&dst[0], &src[0], size)
        
        return dst
