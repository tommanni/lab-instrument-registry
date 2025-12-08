import { setActivePinia, createPinia } from 'pinia'
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { useDataStore } from '@/stores/data'
import axios from 'axios'
import Fuse from 'fuse.js'

// Mock dependencies
vi.mock('axios')
vi.mock('vue-router', () => ({
    useRoute: vi.fn(() => ({ query: {} })),
    useRouter: vi.fn(() => ({ replace: vi.fn().mockResolvedValue() }))
}))
vi.mock('vue-i18n', () => ({
    useI18n: () => ({ locale: { value: 'fi' } })
}))

// Auto-mock Fuse.js
// This makes 'Fuse' a mock constructor
vi.mock('fuse.js')

describe('useDataStore Smart Search', () => {
    let store

    beforeEach(() => {
        setActivePinia(createPinia())
        store = useDataStore()
        vi.clearAllMocks()
        axios.get.mockResolvedValue({ data: [] })

        // Reset Fuse search mock for each test
        // Since we mocked the module, Fuse.prototype.search should be a spy
        // But sometimes auto-mocking implementation details vary.
        // Let's explicitly define it to be sure.
        Fuse.prototype.search = vi.fn().mockReturnValue([])
    })

    it('smartSearch uses only fuzzy search when results are sufficient (>= 10)', async () => {
        store.originalData = Array(20).fill({ id: 1, name: 'Item' })
        store.filteredData = store.originalData

        // Mock Fuse returning 10 results
        const mockFuseResults = Array(10).fill(0).map((_, i) => ({ item: { id: i, name: `Result ${i}` } }))
        Fuse.prototype.search.mockReturnValue(mockFuseResults)

        store.searchMode = 'smart'
        store.searchTerm = 'test'

        await store.searchData(false)

        expect(store.searchedData).toHaveLength(10)
        expect(axios.get).not.toHaveBeenCalledWith('/api/instruments/search/', expect.any(Object))
    })

    it('smartSearch calls semantic search API when fuzzy results are insufficient (< 10)', async () => {
        store.originalData = [
            { id: 1, name: 'Fuzzy 1' },
            { id: 2, name: 'Fuzzy 2' },
            { id: 3, name: 'Semantic 1' },
            { id: 4, name: 'Semantic 2' },
            { id: 5, name: 'Other' }
        ]

        // Mock Fuse returning only 2 results
        const mockFuseResults = [
            { item: { id: 1, name: 'Fuzzy 1' } },
            { item: { id: 2, name: 'Fuzzy 2' } }
        ]
        Fuse.prototype.search.mockReturnValue(mockFuseResults)

        // Mock Semantic Search API response
        const mockSemanticResults = [
            { id: 3, name: 'Semantic 1' },
            { id: 4, name: 'Semantic 2' }
        ]
        axios.get.mockResolvedValueOnce({ data: mockSemanticResults })

        store.searchMode = 'smart'
        store.searchTerm = 'complex query'

        await store.searchData(false)

        expect(axios.get).toHaveBeenCalledWith('/api/instruments/search/', {
            params: { q: 'complex query' },
            withCredentials: true
        })

        expect(store.searchedData).toHaveLength(4)
        const ids = store.searchedData.map(i => i.id).sort()
        expect(ids).toEqual([1, 2, 3, 4])
    })

    it('smartSearch merges and deduplicates results correctly', async () => {
        const items = [
            { id: 1, name: 'Overlapping Item' },
            { id: 2, name: 'Semantic Only' }
        ]
        store.originalData = items

        // Fuzzy finds ID 1
        Fuse.prototype.search.mockReturnValue([{ item: items[0] }])

        // Semantic finds ID 1 and ID 2
        axios.get.mockResolvedValueOnce({ data: items })

        store.searchMode = 'smart'
        store.searchTerm = 'overlap'

        await store.searchData(false)

        expect(store.searchedData).toHaveLength(2)
        const ids = store.searchedData.map(i => i.id).sort()
        expect(ids).toEqual([1, 2])
    })

    it('smartSearch filters out semantic results that do not match current filters', async () => {
        // Scenario: User filters by "Unit A". Semantic search returns an item from "Unit B".
        // The item from Unit B should be discarded.

        const allowedItems = [{ id: 1, name: 'Allowed Item' }]
        store.originalData = allowedItems // These represent the currently filtered items

        // Fuzzy finds nothing
        Fuse.prototype.search.mockReturnValue([])

        // Semantic API finds a result that is NOT in the allowed items
        const forbiddenItem = { id: 99, name: 'Forbidden Item' }
        axios.get.mockResolvedValueOnce({ data: [forbiddenItem] })

        store.searchMode = 'smart'
        store.searchTerm = 'query'

        await store.searchData(false)

        expect(store.searchedData).toHaveLength(0)
    })

    it('smartSearch handles API errors gracefully', async () => {
        const items = [{ id: 1, name: 'Fuzzy' }]
        store.originalData = items

        Fuse.prototype.search.mockReturnValue([{ item: items[0] }])

        // Semantic search fails
        axios.get.mockRejectedValueOnce(new Error('Network Error'))
        const consoleSpy = vi.spyOn(console, 'error').mockImplementation(() => { })

        store.searchMode = 'smart'
        store.searchTerm = 'error'

        await store.searchData(false)

        expect(store.searchedData).toHaveLength(1)
        expect(store.searchedData[0].id).toBe(1)
        expect(consoleSpy).toHaveBeenCalled()
    })
})
