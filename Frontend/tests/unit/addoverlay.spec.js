// Mock instances
const mockShowAlert = vi.fn()
const mockAddObject = vi.fn()

// Mock axios
vi.mock('axios', () => ({
  default: {
    post: vi.fn(() => Promise.resolve({ data: {} }))
  }
}))

// Mock stores using the same spy instances
vi.mock('@/stores/data', () => ({
  useDataStore: () => ({
    isLoggedIn: true,
    addObject: mockAddObject
  })
}))

vi.mock('@/stores/alert', () => ({
  useAlertStore: () => ({
    showAlert: mockShowAlert
  })
}))

import { describe, it, expect, vi, beforeEach } from 'vitest'
import { mount } from '@vue/test-utils'
import { createI18n } from 'vue-i18n'
import AddOverlay from '@/components/AddOverlay.vue'

const i18n = createI18n({
  legacy: false,
  globalInjection: true,
  locale: 'en',
  messages: {
    en: {
      message: {
        uusi_laite: 'New Device',
        tiedot_uusi: 'Enter New Device Info',
        tuotenimi: 'Product Name',
        sarjanumero: 'Serial Number',
        kampus: 'Campus',
        huone: 'Room',
        pvm: 'Delivery Date',
        lisatieto: 'Additional Info',
        huoltosopimus_loppuu: 'Maintenance Contract Ends',
        tay: 'TAY Number',
        merkki: 'Brand/Model',
        yksikko: 'Unit',
        rakennus: 'Building',
        vastuuhenkilo: 'Responsible Person',
        toimittaja: 'Supplier',
        edellinen_huolto: 'Last Maintenance',
        seuraava_huolto: 'Next Maintenance',
        tallenna: 'Save',
        lisattu: 'added'
      }
    }
  }
})

describe('AddOverlay.vue', () => {
  let wrapper

  beforeEach(() => {
    vi.clearAllMocks()
    wrapper = mount(AddOverlay, {
      global: {
        plugins: [i18n]
      }
    })
  })

  it('renders open button when logged in', () => {
    const button = wrapper.find('button.add-button')
    expect(button.exists()).toBe(true)
    expect(button.text()).toBe('New Device')
  })

  it('opens and closes the overlay', async () => {
    const openBtn = wrapper.find('button.add-button')
    await openBtn.trigger('click')

    expect(wrapper.vm.showOverlay).toBe(true)
    expect(wrapper.find('.overlay-backdrop').exists()).toBe(true)

    const closeBtn = wrapper.find('button.close-button')
    await closeBtn.trigger('click')

    expect(wrapper.vm.showOverlay).toBe(false)
  })

  it('updates formData and calls saveData', async () => {
    await wrapper.find('button.add-button').trigger('click')
    await wrapper.find('#tuotenimi').setValue('Test Device')

    expect(wrapper.vm.formData.tuotenimi).toBe('Test Device')

    await wrapper.find('button.save-button').trigger('click')

    expect(mockShowAlert).toHaveBeenCalledWith(0, 'Test Device added')
    expect(mockAddObject).toHaveBeenCalled()
    expect(wrapper.vm.showOverlay).toBe(false)
  })
})