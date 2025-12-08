import { describe, it, expect, vi, beforeEach } from 'vitest'
import { mount } from '@vue/test-utils'
import { createI18n } from 'vue-i18n'
import AddOverlay from '@/components/AddOverlay.vue'
import axios from 'axios'

// Mock instances
const mockShowAlert = vi.fn()
const mockAddObject = vi.fn()

// Mock axios
vi.mock('axios', () => ({
  default: {
    post: vi.fn(() => Promise.resolve({ data: { id: 1, tuotenimi: 'Test Device' } }))
  }
}))

// Mock stores
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
        lisatty: 'added',
        ei_lisatty: 'failed to add',
        peruuta: 'Cancel',
        vaaditaan: 'required'
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

  it('renders the add button', () => {
    const button = wrapper.find('button.btn.btn-primary');
    expect(button.exists()).toBe(true);
    expect(button.text()).toBe('New Device');
  })

  it('saves data and emits event on save button click', async () => {
    // Set required form data
    wrapper.vm.formData.tuotenimi = 'Test Device'
    wrapper.vm.formData.merkki_ja_malli = 'Test Brand'
    wrapper.vm.formData.kampus = 'Test Campus'

    // Call saveData directly
    await wrapper.vm.saveData()

    expect(axios.post).toHaveBeenCalled()
    expect(mockShowAlert).toHaveBeenCalledWith(0, expect.stringContaining('added'))
    expect(mockAddObject).toHaveBeenCalled()
  })

})