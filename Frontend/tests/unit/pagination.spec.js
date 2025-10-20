import { describe, it, expect, vi, beforeEach } from 'vitest'
import { mount } from '@vue/test-utils'
import { createI18n } from 'vue-i18n'
import Pagination from '@/components/Pagination.vue'

// Mock store setup
const mockUpdateVisibleData = vi.fn()
let currentPage = 1
let numberOfPages = 10

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

const i18n = createI18n({
  legacy: false,
  globalInjection: true,
  locale: 'en',
  messages: {
    en: {
      message: {
        edellinen: '<<Previous',
        seuraava: 'Next'
      }
    }
  }
})

describe('Pagination.vue', () => {
  let wrapper

  beforeEach(() => {
    currentPage = 1
    numberOfPages = 10
    mockUpdateVisibleData.mockReset()

    wrapper = mount(Pagination, {
      global: {
        plugins: [i18n]
      }
    })
  })

  it('renders previous and next buttons', () => {
    const links = wrapper.findAll('.page-link')
    expect(links[0].text()).toContain('Previous') // Use `toContain` to allow for additional characters
    expect(links[links.length - 1].text()).toContain('Next')
  })

  it('disables previous button on the first page', () => {
    const prevButton = wrapper.find('li.page-item:first-child')
    expect(prevButton.classes()).toContain('disabled')
  })

  it('disables next button on the last page', async () => {
    currentPage = 10
    wrapper = mount(Pagination, {
      global: {
        plugins: [i18n]
      }
    })

    const nextButton = wrapper.find('li.page-item:last-child')
    expect(nextButton.classes()).toContain('disabled')
  })

  it('changes page when a page number is clicked', async () => {
    const pageButton = wrapper.findAll('.page-link').find(btn => btn.text() === '3')
    await pageButton.trigger('click')

    expect(currentPage).toBe(3)
  })

  it('does not go below page 1 or above the last page', async () => {
    const prevButton = wrapper.find('li.page-item:first-child .page-link')
    await prevButton.trigger('click')
    expect(currentPage).toBe(1)

    currentPage = 10
    wrapper = mount(Pagination, {
      global: {
        plugins: [i18n]
      }
    })
    const nextButton = wrapper.find('li.page-item:last-child .page-link')
    await nextButton.trigger('click')
    expect(currentPage).toBe(10)
  })
})