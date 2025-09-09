import { mount, flushPromises } from '@vue/test-utils'
import { describe, it, expect, vi, beforeEach } from 'vitest'
import Filter from '@/components/Filter.vue'
import { createI18n } from 'vue-i18n'
import axios from 'axios'

// Mock axios response
vi.mock('axios')

const mockFilterData = {
  data: {
    data: ['Option 1', 'Option 2', 'Test Option']
  }
}

axios.get.mockResolvedValue(mockFilterData)

const i18n = createI18n({
  legacy: false,
  globalInjection: true,
  locale: 'en',
  messages: {
    en: {
      message: {
        yksikko: 'Unit',
        huone: 'Room',
        vastuuhenkilo: 'Responsible Person',
        tilanne: 'Status',
        suodatin: 'Filter',
        placeholder: 'Search...'
      }
    }
  }
})

describe('Filter.vue', () => {
  let wrapper

  beforeEach(async () => {
    wrapper = mount(Filter, {
      global: {
        plugins: [i18n]
      }
    })
    await flushPromises()
  })

  it('renders all filters with correct titles', () => {
    const categories = wrapper.findAll('.category')
    expect(categories.length).toBe(4)
    expect(categories[0].text()).toContain('Unit')
    expect(categories[1].text()).toContain('Room')
    expect(categories[2].text()).toContain('Responsible Person')
    expect(categories[3].text()).toContain('Status')
  })

  it('toggles dropdown visibility on category click', async () => {
    const category = wrapper.findAll('.category')[0]
    await category.trigger('click')
    expect(wrapper.find('.dropdown-content').exists()).toBe(true)

    await category.trigger('click')
    expect(wrapper.find('.dropdown-content').exists()).toBe(false)
  })

  it('shows options from API and filters them based on input', async () => {
    const category = wrapper.findAll('.category')[0]
    await category.trigger('click')
    await flushPromises()

    const input = wrapper.find('input')
    await input.setValue('Test')
    await flushPromises()

    const options = wrapper.findAll('.option')
    expect(options.length).toBe(1)
    expect(options[0].text()).toContain('Test Option')
  })

  it('emits filter-change event on option select', async () => {
    const category = wrapper.findAll('.category')[0]
    await category.trigger('click')
    await flushPromises()

    const option = wrapper.findAll('.option')[1]
    await option.trigger('click')

    expect(wrapper.emitted()['filter-change']).toBeTruthy()
    const emitted = wrapper.emitted()['filter-change'][0][0]
    expect(emitted.filterName).toBe('yksikko')
    expect(emitted.value).toBe('Option 2')
  })

  it('clears selection and emits filter-change on clear button click', async () => {
    // Select an option first
    const category = wrapper.findAll('.category')[0]
    await category.trigger('click')
    await flushPromises()
    const option = wrapper.findAll('.option')[0]
    await option.trigger('click')

    // Clear it
    const clearBtn = wrapper.find('.reset-button')
    await clearBtn.trigger('click')

    const lastEmit = wrapper.emitted()['filter-change'].pop()[0]
    expect(lastEmit.filterName).toBe('yksikko')
    expect(lastEmit.value).toBe(null)
  })
})