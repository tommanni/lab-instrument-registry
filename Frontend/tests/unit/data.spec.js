import { describe, it, expect, vi, beforeEach } from 'vitest'
import { mount } from '@vue/test-utils'
import { createI18n } from 'vue-i18n'
import Data from '@/components/Data.vue'
import { ref } from 'vue'

// Mock instances
const mockShowAlert = vi.fn()


// Mock stores
vi.mock('@/stores/data', () => ({
  useDataStore: () => ({
    data: [
      { id: 1, tuotenimi: 'Testi', tuotenimi_en: 'Test', merkki_ja_malli: 'M1', kampus: 'K', huone: '101', vastuuhenkilo: 'A', tilanne: 'Saatavilla' },
      { id: 2, tuotenimi: 'Testi 2', tuotenimi_en: 'Test 2', merkki_ja_malli: 'M2', kampus: 'K', huone: '101', vastuuhenkilo: 'A', tilanne: 'Saatavilla' }
    ],
    searchedData: [
      { id: 1, tuotenimi: 'Testi', tuotenimi_en: 'Test', merkki_ja_malli: 'M1', kampus: 'K', huone: '101', vastuuhenkilo: 'A', tilanne: 'Saatavilla' },
      { id: 2, tuotenimi: 'Testi 2', tuotenimi_en: 'Test 2', merkki_ja_malli: 'M2', kampus: 'K', huone: '101', vastuuhenkilo: 'A', tilanne: 'Saatavilla' }
    ],
    currentPage: ref(1),
    numberOfPages: ref(1),
    isLoggedIn: true,
    locale: 'fi',
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
  locale: 'fi',
})

describe('Data.vue', () => {
  let wrapper

  beforeEach(() => {
    vi.clearAllMocks()
    wrapper = mount(Data, {
      global: {
        plugins: [i18n],
        mocks: {
          $tm: () => ['Tuotenimi','Merkki ja malli','Kampus','Huone','Vastuuhenkilö','Tilanne']
        }
      },
    })
  })

  it('renders the data table correctly', () => {
    const rows = wrapper.findAll('tbody tr')

    expect(rows.length).toBe(2)

    expect(rows[0].text()).toContain('Testi')
    expect(rows[0].text()).toContain('M1')

    expect(rows[1].text()).toContain('Testi 2')
    expect(rows[1].text()).toContain('M2')
  })
})