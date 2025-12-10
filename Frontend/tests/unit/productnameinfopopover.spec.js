import { mount } from '@vue/test-utils'
import { describe, it, expect, vi, beforeEach } from 'vitest'
import ProductNameInfoPopover from '@/components/ProductNameInfoPopover.vue'
import { ref, nextTick } from 'vue'

// Use vi.hoisted to create mocks that can be used in vi.mock and tests
const mocks = vi.hoisted(() => {
    const dispose = vi.fn()
    const instance = { dispose }
    const constructor = vi.fn(() => instance)
    return {
        dispose,
        instance,
        constructor
    }
})

vi.mock('bootstrap', () => ({
    Popover: mocks.constructor
}))

// Mock Vue I18n
const locale = ref('en')
vi.mock('vue-i18n', () => ({
    useI18n: () => ({
        t: (key) => key,
        locale
    })
}))

describe('ProductNameInfoPopover.vue', () => {

    beforeEach(() => {
        vi.clearAllMocks()
        locale.value = 'en'
    })

    it('renders button when locale is en', () => {
        const wrapper = mount(ProductNameInfoPopover)
        expect(wrapper.find('button').exists()).toBe(true)
    })

    it('does NOT render button when locale is not en', async () => {
        locale.value = 'fi'
        const wrapper = mount(ProductNameInfoPopover)
        expect(wrapper.find('button').exists()).toBe(false)
    })

    it('initializes Popover on mount when locale is en', async () => {
        const wrapper = mount(ProductNameInfoPopover)
        await nextTick()

        expect(mocks.constructor).toHaveBeenCalled()
        expect(mocks.constructor).toHaveBeenCalledWith(
            expect.any(Object),
            expect.objectContaining({ trigger: 'hover focus' })
        )
    })

    it('disposes Popover on unmount', async () => {
        const wrapper = mount(ProductNameInfoPopover)
        await nextTick()

        wrapper.unmount()

        expect(mocks.dispose).toHaveBeenCalled()
    })

    it('re-initializes Popover when locale changes to en', async () => {
        locale.value = 'fi'
        const wrapper = mount(ProductNameInfoPopover)
        expect(mocks.constructor).not.toHaveBeenCalled()

        locale.value = 'en'
        await nextTick()
        await nextTick()

        expect(mocks.constructor).toHaveBeenCalled()
    })
})
