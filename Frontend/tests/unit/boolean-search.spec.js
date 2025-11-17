import { describe, it, expect, vi, beforeEach } from 'vitest'
import { createPinia, setActivePinia } from 'pinia'
import { useDataStore } from '@/stores/data'

// Mock i18n and router used inside the store
vi.mock('vue-i18n', () => ({
  useI18n: () => ({ locale: { value: 'en' } })
}))

const replaceMock = vi.fn(() => Promise.resolve())
vi.mock('vue-router', () => ({
  useRoute: () => ({ query: {}, path: '/' }),
  useRouter: () => ({ replace: replaceMock })
}))

describe('Boolean search (useDataStore)', () => {
  let store

  const items = [
    {
      id: 1,
      tuotenimi: 'Electron Microscope',
      tuotenimi_en: 'Electron Microscope',
      merkki_ja_malli: 'Zeiss EM-100',
      tay_numero: 'TAY-001',
      sarjanumero: 'SN-123',
      yksikko: 'Physics',
      kampus: 'Main',
      rakennus: 'Lab A',
      huone: 'A101',
      vastuuhenkilo: 'Alice',
      tilanne: 'active',
      lisatieto: 'high resolution'
    },
    {
      id: 2,
      tuotenimi: 'Optical Microscope',
      tuotenimi_en: 'Optical Microscope',
      merkki_ja_malli: 'Nikon OptiMax',
      tay_numero: 'TAY-002',
      sarjanumero: 'SN-456',
      yksikko: 'Biology',
      kampus: 'Main',
      rakennus: 'Lab B',
      huone: 'B202',
      vastuuhenkilo: 'Bob',
      tilanne: 'retired',
      lisatieto: 'old device'
    },
    {
      id: 3,
      tuotenimi: 'Centrifuge',
      tuotenimi_en: 'Centrifuge',
      merkki_ja_malli: 'Eppendorf 5418',
      tay_numero: 'TAY-003',
      sarjanumero: 'SN-789',
      yksikko: 'Biology',
      kampus: 'Main',
      rakennus: 'Lab B',
      huone: 'B203',
      vastuuhenkilo: 'Carol',
      tilanne: 'active',
      lisatieto: 'compact'
    }
  ]

  beforeEach(() => {
    setActivePinia(createPinia())
    vi.clearAllMocks()
    store = useDataStore()
    // Initialize store state
    store.originalData = items
    store.filteredData = items
    store.searchedData = items
    store.currentPage = 1
    store.searchMode = 'direct'
    store.filterValues = { yksikko: null, huone: null, vastuuhenkilo: null, tilanne: null }
  })

  it('matches single field query using finnish field name', async () => {
    store.searchTerm = 'tuotenimi: microscope'
    await store.searchData(false)
    const resultIds = store.searchedData.map(i => i.id)
    expect(resultIds.sort()).toEqual([1, 2])
    expect(replaceMock).toHaveBeenCalled() // URL updated
  })

  it('supports AND between field conditions', async () => {
    store.searchTerm = 'product_name: microscope AND tilanne: active'
    await store.searchData(false)
    const resultIds = store.searchedData.map(i => i.id)
    expect(resultIds).toEqual([1])
  })

  it('supports OR between field conditions', async () => {
    store.searchTerm = 'tilanne: active OR tilanne: retired'
    await store.searchData(false)
    const resultIds = store.searchedData.map(i => i.id)
    expect(resultIds.sort()).toEqual([1, 2, 3])
  })

  it('supports NOT to exclude matches', async () => {
    store.searchTerm = 'tuotenimi: microscope AND NOT tilanne: retired'
    await store.searchData(false)
    const resultIds = store.searchedData.map(i => i.id)
    expect(resultIds).toEqual([1])
  })

  it('resolves english field aliases (brand_and_model, tay_number)', async () => {
    store.searchTerm = 'brand_and_model: nikon OR tay_number: TAY-003'
    await store.searchData(false)
    const resultIds = store.searchedData.map(i => i.id).sort()
    expect(resultIds).toEqual([2, 3])
  })

  it('matches by id and room using OR', async () => {
    store.searchTerm = 'id: 3 OR huone: A101'
    await store.searchData(false)
    const resultIds = store.searchedData.map(i => i.id).sort()
    expect(resultIds).toEqual([1, 3])
  })

  it('returns all items when search term is empty or whitespace', async () => {
    store.searchTerm = '   '
    await store.searchData(false)
    const resultIds = store.searchedData.map(i => i.id).sort()
    expect(resultIds).toEqual([1, 2, 3])
    expect(replaceMock).toHaveBeenCalled()
  })

  it('handles unknown field name (no matches)', async () => {
    store.searchTerm = 'unknown_field: anything'
    await store.searchData(false)
    expect(store.searchedData.length).toBe(0)
  })

  it('unknown field with OR falls back to the valid side', async () => {
    store.searchTerm = 'unknown_field: anything OR tilanne: active'
    await store.searchData(false)
    const resultIds = store.searchedData.map(i => i.id).sort()
    expect(resultIds).toEqual([1, 3])
  })

  it('is case-insensitive for fields and operators', async () => {
    store.searchTerm = 'PrOdUcT_NaMe: MICROSCOPE aNd TiLaNNe: AcTiVe'
    await store.searchData(false)
    const resultIds = store.searchedData.map(i => i.id)
    expect(resultIds).toEqual([1])
  })

  it('supports parentheses for precedence', async () => {
    store.searchTerm = '(tilanne: retired OR huone: B203) AND yksikko: Biology'
    await store.searchData(false)
    const resultIds = store.searchedData.map(i => i.id).sort()
    expect(resultIds).toEqual([2, 3])
  })

  it('supports NOT at the beginning of the query', async () => {
    store.searchTerm = 'NOT tilanne: retired'
    await store.searchData(false)
    const resultIds = store.searchedData.map(i => i.id).sort()
    expect(resultIds).toEqual([1, 3])
  })

  it('returns empty array when value does not exist', async () => {
    store.searchTerm = 'tilanne: scrapped'
    await store.searchData(false)
    expect(store.searchedData).toEqual([])
  })
})


