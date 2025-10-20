import { ref, watch } from 'vue'
import { defineStore } from 'pinia'
import axios from 'axios'

import { parseQueryToRpn, evaluateRpnBoolean } from '../searchUtils/index'

export const useDataStore = defineStore('dataStore', () => {
  const originalData = ref([])
  const data = ref([])
  const filteredData = ref([])
  const searchedData = ref([])
  const currentPage = ref(1)
  const numberOfPages = ref(1)
  const isLoggedIn = ref(false)
  const loginChecked = ref(false)
  const isInitialized = ref(false)
  const sortColumn = ref('')
  const sortDirection = ref('none')
  const searchTerm = ref('')
  const filterValues = ref({
  yksikko: null,
  huone: null,
  vastuuhenkilo: null,
  tilanne: null,
})
 
  const updateVisibleData = () => {
    // Tehdään kopio hakutuloksista
    let displayData = [...searchedData.value]
    
    // Jos lajittelukriteeri on asetettu, lajitellaan data
    if (sortColumn.value && sortDirection.value !== 'none') {
      displayData.sort((a, b) => {
        const valA = (a[sortColumn.value.toLowerCase()] || '').toString().toLowerCase()
        const valB = (b[sortColumn.value.toLowerCase()] || '').toString().toLowerCase()
        const comp = valA.localeCompare(valB)
        return sortDirection.value === 'asc' ? comp : -comp
      })
    }
    
    // Tehdään sivutus lopuksi
    data.value = displayData.slice((currentPage.value - 1) * 15, currentPage.value * 15)
  }

  const matchesBooleanQuery = (item, query) => {

    const fieldAliases = {
      id: 'id',
      tay_number: 'tay_numero',
      tay_numero: 'tay_numero',
      serial_number: 'sarjanumero',
      sarjanumero: 'sarjanumero',
      product_name: 'tuotenimi',
      tuotenimi: 'tuotenimi',
      brand_and_model: 'merkki_ja_malli',
      merkki_ja_malli: 'merkki_ja_malli',
      unit: 'yksikko',
      yksikko: 'yksikko',
      campus: 'kampus',
      kampus: 'kampus',
      building: 'rakennus',
      rakennus: 'rakennus',
      room: 'huone',
      huone: 'huone',
      responsible_person: 'vastuuhenkilo',
      vastuuhenkilo: 'vastuuhenkilo',
      status: 'tilanne',
      tilanne: 'tilanne',
      supplier: 'toimittaja',
      toimittaja: 'toimittaja',
      extra_information: 'lisatieto',
      extra_info: 'lisatieto',
      details: 'lisatieto',
      lisatieto: 'lisatieto',
      old_location: 'vanha_sijainti',
      vanha_sijainti: 'vanha_sijainti',
      delivery_date: 'toimituspvm',
      toimituspvm: 'toimituspvm'
    }

    const getFieldValue = (obj, field) => {
      const canonical = fieldAliases[field] || field
      const v = obj[canonical]
      return v === undefined || v === null ? '' : String(v).toLowerCase()
    }

    const anyFieldIncludes = (lower) => (
      (item.id !== undefined && item.id !== null && item.id.toString().includes(lower)) ||
      (item.tay_numero && item.tay_numero.toLowerCase().includes(lower)) ||
      (item.sarjanumero && item.sarjanumero.toLowerCase().includes(lower)) ||
      (item.toimituspvm && item.toimituspvm.toString().toLowerCase().includes(lower)) ||
      (item.toimittaja && item.toimittaja.toLowerCase().includes(lower)) ||
      (item.lisatieto && item.lisatieto.toLowerCase().includes(lower)) ||
      (item.vanha_sijainti && item.vanha_sijainti.toLowerCase().includes(lower)) ||
      (item.tuotenimi && item.tuotenimi.toLowerCase().includes(lower)) ||
      (item.merkki_ja_malli && item.merkki_ja_malli.toLowerCase().includes(lower)) ||
      (item.yksikko && item.yksikko.toLowerCase().includes(lower)) ||
      (item.kampus && item.kampus.toLowerCase().includes(lower)) ||
      (item.rakennus && item.rakennus.toLowerCase().includes(lower)) ||
      (item.huone && item.huone.toLowerCase().includes(lower)) ||
      (item.vastuuhenkilo && item.vastuuhenkilo.toLowerCase().includes(lower)) ||
      (item.tilanne && item.tilanne.toLowerCase().includes(lower))
    )

    const itemMatchesSingleTerm = (symbol) => {
      const lower = String(symbol.value || '').toLowerCase()
      if (symbol.fieldName) {
        const fieldLower = getFieldValue(item, symbol.fieldName.toLowerCase())
        return fieldLower.includes(lower)
      }
      return anyFieldIncludes(lower)
    }

    const rpn = parseQueryToRpn(query)
    return evaluateRpnBoolean(rpn, item, itemMatchesSingleTerm)
  }

  const fetchData = async () => {
    try {
      const res = await axios.get('/api/instruments/', {
        withCredentials: true
      });
      originalData.value = res.data
      data.value = res.data.slice(0, 15)
      numberOfPages.value = Math.ceil(res.data.length / 15)
      searchedData.value = res.data
      filteredData.value = res.data
    } catch (error) {
      // Error fetching data
    }
  }
  const deleteObject = async (id) => {
    originalData.value = originalData.value.filter(o => o.id !== id)
    filteredData.value = filteredData.value.filter(o => o.id !== id)
    searchedData.value = searchedData.value.filter(o => o.id !== id)
    updateVisibleData()
  }

  const updateObject = (object) => {
    originalData.value = originalData.value.map(obj => 
      obj.id === object.id ? {...obj, ...object} : obj
    )
    filteredData.value = filteredData.value.map(obj => 
      obj.id === object.id ? {...obj, ...object} : obj
    )
    searchedData.value = searchedData.value.map(obj => 
      obj.id === object.id ? {...obj, ...object} : obj
    )
    updateVisibleData()
  }
  const addObject = (object) => {
    originalData.value.push(object)
    updateVisibleData()
  }
  const filterData = ({yksikko, huone, vastuuhenkilo, tilanne}) => {
    // TODO Add cookie flags for live build
    if (yksikko !== undefined) {
    filterValues.value.yksikko = yksikko
    document.cookie = `YksikkoFilter=${encodeURIComponent(yksikko || '')}; Path=/` /*; Secure; SameSite=Strict*/
    }
    if (huone !== undefined) {
      filterValues.value.huone = huone
      document.cookie = `HuoneFilter=${encodeURIComponent(huone || '')}; Path=/` /*; Secure; SameSite=Strict*/
    }
    if (vastuuhenkilo !== undefined) {
      filterValues.value.vastuuhenkilo = vastuuhenkilo
      document.cookie = `VastuuHFilter=${encodeURIComponent(vastuuhenkilo || '')}; Path=/` /*; Secure; SameSite=Strict*/
    }
    if (tilanne !== undefined) {
      filterValues.value.tilanne = tilanne
      document.cookie = `TilanneFilter=${encodeURIComponent(tilanne || '')}; Path=/` /*; Secure; SameSite=Strict*/
    }

    applySearchAndFilter()
  
  }

  function searchData(term) {
    // TODO Add cookie flags for live build
    searchTerm.value = term
    document.cookie = `InstrumentSearchTerm=${encodeURIComponent(searchTerm.value)}; path=/`; /*; Secure; SameSite=Strict*/
    applySearchAndFilter()
}

  function applySearchAndFilter() {
    const lowerSearch = searchTerm.value.toLowerCase()

    // Apply filters
    const filtered = originalData.value.filter(item => {
      let match = true
      if (filterValues.value.yksikko)
        match = match && item.yksikko === filterValues.value.yksikko
      if (filterValues.value.huone)
        match = match && item.huone === filterValues.value.huone
      if (filterValues.value.vastuuhenkilo)
        match = match && item.vastuuhenkilo === filterValues.value.vastuuhenkilo
      if (filterValues.value.tilanne)
        match = match && item.tilanne === filterValues.value.tilanne
      return match
    })

    filteredData.value = filtered

    // Apply search term
    let results = filtered
    if (lowerSearch) {
      const hasBooleanOperator = /\b(AND|OR|NOT)\b/i.test(searchTerm.value) || /\b[A-Za-z_][A-Za-z0-9_]*\s*:/i.test(searchTerm.value)
      if (hasBooleanOperator) {
        results = filtered.filter((item) => matchesBooleanQuery(item, searchTerm.value))
      } else { 
        results = filtered.filter((item) =>
          (item.id.toString().includes(lowerSearch)) ||
          (item.tay_numero && item.tay_numero.toLowerCase().includes(lowerSearch)) ||
          (item.sarjanumero && item.sarjanumero.toLowerCase().includes(lowerSearch)) ||
          (item.toimituspvm && item.toimituspvm.toString().toLowerCase().includes(lowerSearch)) ||
          (item.toimittaja && item.toimittaja.toLowerCase().includes(lowerSearch)) ||
          (item.lisatieto && item.lisatieto.toLowerCase().includes(lowerSearch)) ||
          (item.vanha_sijainti && item.vanha_sijainti.toLowerCase().includes(lowerSearch)) ||
          (item.tuotenimi && item.tuotenimi.toLowerCase().includes(lowerSearch)) ||
          (item.merkki_ja_malli && item.merkki_ja_malli.toLowerCase().includes(lowerSearch)) ||
          (item.yksikko && item.yksikko.toLowerCase().includes(lowerSearch)) ||
          (item.kampus && item.kampus.toLowerCase().includes(lowerSearch)) ||
          (item.rakennus && item.rakennus.toLowerCase().includes(lowerSearch)) ||
          (item.huone && item.huone.toLowerCase().includes(lowerSearch)) ||
          (item.vastuuhenkilo && item.vastuuhenkilo.toLowerCase().includes(lowerSearch)) ||
          (item.tilanne && item.tilanne.toLowerCase().includes(lowerSearch))
        )
      }
    }
    searchedData.value = results
    currentPage.value = 1
    numberOfPages.value = Math.ceil(results.length / 15)

    updateVisibleData()
  }

  // Function for data initialization based on active filters
  const initializePageFromCookies = () => {
    
    const cookies = Object.fromEntries(
    document.cookie.split('; ').map(cookie => {
      const [key, ...rest] = cookie.split('=')
      return [key.trim(), rest.join('=')]
    })
  )

  const FilterCookies = {}

  if (cookies.YksikkoFilter) {
    FilterCookies.yksikko = decodeURIComponent(cookies.YksikkoFilter)
  }
  if (cookies.HuoneFilter) {
    FilterCookies.huone = decodeURIComponent(cookies.HuoneFilter)
  }
  if (cookies.VastuuHFilter) {
    FilterCookies.vastuuhenkilo = decodeURIComponent(cookies.VastuuHFilter)
  }
  if (cookies.TilanneFilter) {
    FilterCookies.tilanne = decodeURIComponent(cookies.TilanneFilter)
  }

  if (Object.keys(FilterCookies).length > 0) {
    filterData(FilterCookies)
  }

  if (cookies.InstrumentSearchTerm) {
    searchData(decodeURIComponent(cookies.InstrumentSearchTerm))
  }

  if (cookies.CurrentPage) {
    const page = parseInt(cookies.CurrentPage, 10)
    if (!isNaN(page)) {
      currentPage.value = page
    }
  }

    updateVisibleData()
  }
  // TODO Add cookie flags for live build
  watch(currentPage, (newPage) => {
    document.cookie = `CurrentPage=${newPage}; Path=/` /*; Secure; SameSite=Strict*/
  })
  

  return { 
    data, 
    numberOfPages, 
    currentPage, 
    fetchData, 
    filterData, 
    updateVisibleData, 
    searchData, 
    deleteObject, 
    updateObject, 
    addObject, 
    filteredData, 
    searchedData, 
    isLoggedIn,
    sortColumn, 
    sortDirection,
    initializePageFromCookies
  }
})
