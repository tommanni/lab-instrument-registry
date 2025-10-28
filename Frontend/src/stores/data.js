import { ref, watch } from 'vue'
import { defineStore } from 'pinia'
import axios from 'axios'
import { useRoute, useRouter } from 'vue-router'

import { parseQueryToRpn, evaluateRpnBoolean } from '../searchUtils/index'

export const useDataStore = defineStore('dataStore', () => {
  const route = useRoute()
  const router = useRouter()
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
  const filterData = () => {

    currentPage.value = 1

    updateURL()
    applySearchAndFilter()
  
  }

  function searchData(clear) {
    if (clear) {
      searchTerm.value = '';
    }

    currentPage.value = 1

    updateURL()
    applySearchAndFilter()
  }

  function updateURL() {

    const query = { ...route.query}

    Object.entries(filterValues.value).forEach(([key, value]) => {
      if (value !== null && value !== '') {
        query[key] = value
      } else {
        delete query[key]
      }
    });

    if (searchTerm.value && searchTerm.value.trim() !== '') {
      query.search = searchTerm.value.trim()
    } else {
      delete query.search
    }

    if (currentPage.value && currentPage.value > 1) {
      query.page = String(currentPage.value)
    } else {
      delete query.page
    }

    router.replace({ query }).catch(() => {})
  }

  // Keep URL and visible data in sync when page changes
  watch(currentPage, (newPage) => {
    // normalize and clamp page
    const p = Number.isNaN(Number(newPage)) ? 1 : Number(newPage)
    if (p < 1) {
      currentPage.value = 1
      return
    }
    if (numberOfPages.value && p > numberOfPages.value) {
      currentPage.value = numberOfPages.value
      return
    }

    // Update the URL and visible slice whenever page changes
    updateURL()
    updateVisibleData()
  })

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
      const searchTermSanitized = searchTerm.value.trim().replace(/\s+/g, " ").toLowerCase(); //Trims whitespaces from beginning and end and replace identifies additinal whitespaces between words
      const hasBooleanOperator = /\b(AND|OR|NOT)\b/i.test(searchTermSanitized) || /\b[A-Za-z_][A-Za-z0-9_]*\s*:/i.test(searchTermSanitized)
      if (hasBooleanOperator) {
        results = filtered.filter((item) => matchesBooleanQuery(item, searchTermSanitized))
      } else { 
        results = filtered.filter((item) =>
          (item.id.toString().includes(searchTermSanitized)) ||
          (item.tay_numero && item.tay_numero.toLowerCase().includes(searchTermSanitized)) ||
          (item.sarjanumero && item.sarjanumero.toLowerCase().includes(searchTermSanitized)) ||
          (item.toimituspvm && item.toimituspvm.toString().toLowerCase().includes(searchTermSanitized)) ||
          (item.toimittaja && item.toimittaja.toLowerCase().includes(searchTermSanitized)) ||
          (item.lisatieto && item.lisatieto.toLowerCase().includes(searchTermSanitized)) ||
          (item.vanha_sijainti && item.vanha_sijainti.toLowerCase().includes(searchTermSanitized)) ||
          (item.tuotenimi && item.tuotenimi.toLowerCase().includes(searchTermSanitized)) ||
          (item.merkki_ja_malli && item.merkki_ja_malli.toLowerCase().includes(searchTermSanitized)) ||
          (item.yksikko && item.yksikko.toLowerCase().includes(searchTermSanitized)) ||
          (item.kampus && item.kampus.toLowerCase().includes(searchTermSanitized)) ||
          (item.rakennus && item.rakennus.toLowerCase().includes(searchTermSanitized)) ||
          (item.huone && item.huone.toLowerCase().includes(searchTermSanitized)) ||
          (item.vastuuhenkilo && item.vastuuhenkilo.toLowerCase().includes(searchTermSanitized)) ||
          (item.tilanne && item.tilanne.toLowerCase().includes(searchTermSanitized))
        )
      }
    }
    searchedData.value = results
    numberOfPages.value = Math.ceil(results.length / 15)

    updateVisibleData()

  }

  // Function for data initialization based on active filters
  const initializePageFromURL = () => {

    Object.keys(filterValues.value).forEach((key)  => {
      filterValues.value[key] = route.query[key] ?? null
    });

    searchTerm.value = route.query.search ?? ''

    const p = route.query.page ? parseInt(route.query.page, 10) : 1
    currentPage.value = Number.isNaN(p) ? 1 : p

    applySearchAndFilter()
  }

  // Watcher for filter/search/pagination changes
  watch(() => route.query, (newQuery) => {
    if (route.path !== '/') return

    Object.keys(filterValues.value).forEach(key => {
      filterValues.value[key] = newQuery[key] ?? null
    })

    searchTerm.value = newQuery.search ?? ''

    const p = newQuery.page ? parseInt(newQuery.page, 10) : 1
    currentPage.value = Number.isNaN(p) ? 1 : p

    applySearchAndFilter()

  }, {immediate: false})

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
    filterValues,
    searchTerm,
    initializePageFromURL
  }
})
