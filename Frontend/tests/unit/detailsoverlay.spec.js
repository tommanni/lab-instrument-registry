import { describe, it, expect, vi, beforeEach } from 'vitest'
import { mount } from '@vue/test-utils'
import { createI18n } from 'vue-i18n'
import DetailsOverlay from '@/components/DetailsOverlay.vue'
import axios from 'axios'

// Mock instances
const mockShowAlert = vi.fn()
const mockUpdateObject = vi.fn()
const mockDeleteObject = vi.fn()

// Mock axios
vi.mock('axios', () => ({
  default: {
    put: vi.fn(() => Promise.resolve({ data: { id: 1, tuotenimi: 'Test Device' } })),
    delete: vi.fn(() => Promise.resolve({ data: {} })),
    get: vi.fn(() => Promise.resolve({ data: [] }))
  }
}))

vi.mock('@/stores/alert', () => ({
  useAlertStore: () => ({
    showAlert: mockShowAlert
  })
}))

vi.mock('@/stores/data', () => ({
  useDataStore: () => ({
    isLoggedIn: true,
    originalData: [],
    updateObject: mockUpdateObject,
    deleteObject: mockDeleteObject
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
        tiedot_nykyinen: 'Current Device Info',
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
        vaaditaan: 'required',
        poistettu: 'deleted',
        poisto_teksti: 'Are you sure you want to delete this item?',
        kylla_poisto: 'Yes, delete',
        on_paivitetty: 'Updated successfully',
        ei_paivitetty: 'Failed to update',
        virhe: 'Error',
        tuntematon_virhe: 'Unknown error',
        takaisin: 'Back',
        muokkaa: 'Edit',
        paivita: 'Update',
        muutoshistoria: 'Change History',
        historia: 'History',
        jarjestelma: 'System'
      }
    }
  }
})

describe('DetailsOverlay.vue', () => {
  let wrapper

  beforeEach(() => {
    vi.clearAllMocks()
    wrapper = mount(DetailsOverlay, {
      global: {
        plugins: [i18n],
      },
      props: {
        item: { 
          id: 1, 
          tuotenimi: 'Test Device', 
          tuotenimi_en: 'Test',
          merkki_ja_malli: 'Model X',
          kampus: 'Campus A',
          huone: '101',
          vastuuhenkilo: 'John Doe',
          tilanne: 'Saatavilla',
          tay_numero: 'TAY001',
          sarjanumero: 'SN123',
          yksikko: 'pcs',
          rakennus: 'Building A',
          toimittaja: 'Supplier X',
          toimituspvm: '2023-01-01',
          huoltosopimus_loppuu: null,
          edellinen_huolto: null,
          seuraava_huolto: null,
          lisatieto: 'Info'
        },
        allowDelete: true,
      }
    })
  })

  it('deletes data and emits event on confirmDelete', async () => {
    await wrapper.vm.$nextTick()

    await wrapper.vm.confirmDelete()

    await vi.waitFor(() => {
      expect(axios.delete).toHaveBeenCalledWith(
        '/api/instruments/1/',
        { withCredentials: true }
      )
    })
    
    expect(wrapper.emitted('delete-item')).toBeTruthy()
    expect(wrapper.emitted('delete-item')[0]).toEqual([1])
  })

  

  it('saves data and emits event on save button click', async () => {
    await wrapper.vm.$nextTick()
    wrapper.vm.view = 'edit'
    wrapper.vm.updateFormData.merkki_ja_malli = 'Merkki muutettu'
    wrapper.vm.confirmUpdate()
    vi.waitFor(() => {
       expect(axios.put).toHaveBeenCalled() 
    })
  })
})