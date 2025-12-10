import { mount, flushPromises } from '@vue/test-utils'
import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { createPinia, setActivePinia } from 'pinia'
import DataTransferView from '@/views/DataTransferView.vue'
import axios from 'axios'

// Mock dependencies
vi.mock('axios')
vi.mock('vue-i18n', () => ({
    useI18n: () => ({
        t: (key, params) => key + (params ? JSON.stringify(params) : ''),
        locale: { value: 'fi' }
    })
}))

// Mock Alert Store
const mockShowAlert = vi.fn()
vi.mock('@/stores/alert', () => ({
    useAlertStore: () => ({
        showAlert: mockShowAlert
    })
}))

// Mock ImportPreviewModal since we are testing parent logic
vi.mock('@/components/ImportPreviewModal.vue', () => ({
    default: {
        template: '<div data-testid="preview-modal"></div>',
        methods: {
            show: vi.fn(),
            hide: vi.fn()
        }
    }
}))

describe('DataTransferView.vue', () => {
    let wrapper

    beforeEach(() => {
        vi.clearAllMocks()
        vi.useFakeTimers()

        // Default embedding status response (not processing)
        axios.get.mockResolvedValue({
            data: { processing: false, pending_count: 0, failed_count: 0 }
        })

        // Setup Pinia
        setActivePinia(createPinia())
    })

    afterEach(() => {
        vi.useRealTimers()
    })

    // Helper to create wrapper
    const createWrapper = () => {
        const wrapper = mount(DataTransferView, {
            global: {
                plugins: [createPinia()], // Use real pinia, stores are mocked via vi.mock
                stubs: {
                    ImportPreviewModal: true
                }
            }
        })
        return wrapper
    }

    it('polls embedding status on mount', async () => {
        axios.get.mockResolvedValueOnce({
            data: { processing: true, pending_count: 5, failed_count: 0 }
        })

        createWrapper()
        await flushPromises()

        expect(axios.get).toHaveBeenCalledWith('/api/embedding-status/', expect.any(Object))
        // Should continue polling because processing was true
        vi.advanceTimersByTime(1100)
        expect(axios.get).toHaveBeenCalledTimes(2) // 1 initial + 1 polled
    })

    it('stops polling when processing is complete', async () => {
        axios.get.mockResolvedValue({
            data: { processing: true, pending_count: 5, failed_count: 0 }
        })

        createWrapper()
        await flushPromises()

        // First poll check done

        // Change mock to finished
        axios.get.mockResolvedValue({
            data: { processing: false, pending_count: 0, failed_count: 0 }
        })

        vi.advanceTimersByTime(1100)
        await flushPromises()

        // Should have called again
        // And stopped subsequent polls
        const callCountBefore = axios.get.mock.calls.length

        vi.advanceTimersByTime(1100)
        expect(axios.get).toHaveBeenCalledTimes(callCountBefore) // No new calls
    })

    it('shows success alert when imports finish successfully', async () => {
        // Simulate polling active state
        axios.get.mockResolvedValue({
            data: { processing: true, pending_count: 5, failed_count: 0 }
        })
        createWrapper()
        await flushPromises()

        // Simulate completion success
        axios.get.mockResolvedValue({
            data: { processing: false, pending_count: 0, failed_count: 0 }
        })

        vi.advanceTimersByTime(1100)
        await flushPromises()

        expect(mockShowAlert).toHaveBeenCalledWith(0, expect.stringContaining('import_prosessointi_valmis'))
    })

    it('shows error alert if failures occurred during processing', async () => {
        // Simulate polling active
        axios.get.mockResolvedValue({
            data: { processing: true, pending_count: 5, failed_count: 0 }
        })
        createWrapper()
        await flushPromises()

        // Simulate completion with failures
        axios.get.mockResolvedValue({
            data: { processing: false, pending_count: 0, failed_count: 3 }
        })

        vi.advanceTimersByTime(1100)
        await flushPromises()

        expect(mockShowAlert).toHaveBeenCalledWith(1, expect.stringContaining('import_prosessointi_epaonnistui'))
    })
})
