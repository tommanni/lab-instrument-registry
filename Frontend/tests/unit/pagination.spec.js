// Mock store setup
const mockUpdateVisibleData = vi.fn()
let currentPage = 1
let numberOfPages = 5

vi.mock('@/stores/data', () => ({
  useDataStore: () => ({
    get currentPage() {
      return currentPage
    },
    set currentPage(val) {
      currentPage = val
    },
    get numberOfPages() {
      return numberOfPages
    },
    updateVisibleData: mockUpdateVisibleData
  })
}))

import { describe, it, expect, vi, beforeEach } from 'vitest'
import { mount } from '@vue/test-utils'
import { createI18n } from 'vue-i18n'
import Pagination from '@/components/Pagination.vue'

const i18n = createI18n({
  legacy: false,
  globalInjection: true,
  locale: 'en',
  messages: {
    en: {
      message: {
        edellinen: 'Previous',
        seuraava: 'Next'
      }
    }
  }
})

describe('Pagination.vue', () => {
  let wrapper

  beforeEach(() => {
    currentPage = 1
    numberOfPages = 5
    mockUpdateVisibleData.mockReset()

    wrapper = mount(Pagination, {
      global: {
        plugins: [i18n]
      }
    })
  })

  it('renders previous and next buttons', () => {
    const links = wrapper.findAll('.page-link')
    expect(links[0].text()).toBe('Previous')
    expect(links[links.length - 1].text()).toBe('Next')
  })

  it('disables previous button on first page', () => {
    expect(wrapper.find('li.page-item.disabled .page-link').text()).toBe('Previous')
  })

  it('calls changePage and updates store on next click', async () => {
    const next = wrapper.findAll('.page-link').find(btn => btn.text() === 'Next')
    await next.trigger('click')

    expect(currentPage).toBe(2)
    expect(mockUpdateVisibleData).toHaveBeenCalled()
  })

  it('calls changePage with specific number when page number clicked', async () => {
    const btn = wrapper.findAll('.page-link').find(b => b.text() === '3')
    await btn.trigger('click')

    expect(currentPage).toBe(3)
    expect(mockUpdateVisibleData).toHaveBeenCalled()
  })

  it('disables next button on last page', async () => {
    currentPage = 5
    wrapper = mount(Pagination, {
      global: {
        plugins: [i18n]
      }
    })

    expect(wrapper.find('li.page-item.disabled .page-link').text()).toBe('Next')
  })

  it('does not go below page 1 or above numberOfPages', async () => {
    await wrapper.findAll('.page-link').find(b => b.text() === 'Previous').trigger('click')
    expect(currentPage).toBe(1)

    currentPage = 5
    wrapper = mount(Pagination, { global: { plugins: [i18n] } })
    await wrapper.findAll('.page-link').find(b => b.text() === 'Next').trigger('click')
    expect(currentPage).toBe(5)
  })
})