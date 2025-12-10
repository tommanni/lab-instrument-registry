import { ref, computed, watch } from 'vue'
import { defineStore } from 'pinia'
import { useRoute, useRouter } from 'vue-router'
import axios from 'axios'

import { parseQueryToRpn, evaluateRpnBoolean } from '../searchUtils/index'

export const useContractStore = defineStore('contractStore', () => {
  // Alkuperäinen data haetaan API:sta
  const originalData = ref([])
  // Kaikki haetut tiedot
  const contractData = ref([])
  // Näytettävä data (sivuittain)
  const data = ref([])
  // Search term
  const searchTerm = ref('')
  const searchedData = ref([])

  // Lajittelukenttä ja suunta (oletuksena seuraava huolto nouseva)
  const sortColumn = ref('seuraava_huolto') 
  const sortDirection = ref('asc')

  // Sivunumeroiden hallinta
  const currentPage = ref(1)
  const numberOfPages = ref(1)

  // guard to avoid clobbering URL/page while initializing
  const isInitialized = ref(false)

  const route = useRoute()
  const router = useRouter()

  const isMaintenanceDue = (dateStr) => {
    if (!dateStr) return false;
    const nextMaintenanceDate = new Date(dateStr);
    const today = new Date();
    // Erotetaan erotus päivissä:
    const diffInDays = (nextMaintenanceDate - today) / (1000 * 60 * 60 * 24);
    return diffInDays <= 0;
  };

  const isMaintenanceUpcoming = (dateStr) => {
    if (!dateStr) return false;
    const nextMaintenanceDate = new Date(dateStr);
    const today = new Date();
    // Erotetaan erotus päivissä:
    const diffInDays = (nextMaintenanceDate - today) / (1000 * 60 * 60 * 24);
    return diffInDays <= 30 && diffInDays >= 0;
  };

  const isUrgent = computed(() =>
    (searchedData.value || []).filter(item => isMaintenanceDue(item.seuraava_huolto)).length
  )
  const isUpcoming = computed(() =>
    (searchedData.value || []).filter(item => isMaintenanceUpcoming(item.seuraava_huolto)).length
  )
  const isEnding = computed(() => 
  (searchedData.value || []).filter(item => isMaintenanceUpcoming(item.huoltosopimus_loppuu)).length
  )
  const isEnded = computed(() => 
  (searchedData.value || []).filter(item => isMaintenanceDue(item.huoltosopimus_loppuu)).length
  )
  const isUrgentNav = computed(() =>
    (contractData.value || []).filter(item => isMaintenanceDue(item.seuraava_huolto)).length
  )
  const isUpcomingNav = computed(() =>
    (contractData.value || []).filter(item => isMaintenanceUpcoming(item.seuraava_huolto)).length
  )
  const isEndingNav = computed(() => 
  (contractData.value || []).filter(item => isMaintenanceUpcoming(item.huoltosopimus_loppuu)).length
  )
  const isEndedNav = computed(() => 
  (contractData.value || []).filter(item => isMaintenanceDue(item.huoltosopimus_loppuu)).length
  )

  // Päivitetään näkyvä data käyttäen suodatettua ja lajiteltua dataa.
  const updateVisibleData = () => {
    // Make copy of searched data to sort and paginate
    let displayData = [...(searchedData.value || [])]

    // Sort by selected column unless sorting is 'none'.
    if (sortColumn.value && sortDirection.value !== 'none') {
      displayData.sort((a, b) => {
        let valA = a[sortColumn.value]
        let valB = b[sortColumn.value]

        const isEmptyA = valA === null || valA === '' || valA === undefined
        const isEmptyB = valB === null || valB === '' || valB === undefined

        // Put empty values last
        if (isEmptyA && !isEmptyB) return 1
        if (!isEmptyA && isEmptyB) return -1
        if (isEmptyA && isEmptyB) return 0

        // Compare dates if both values are valid dates
        const aTime = Date.parse(valA)
        const bTime = Date.parse(valB)

        let cmp
        if (!Number.isNaN(aTime) && !Number.isNaN(bTime)) {
          cmp = aTime - bTime
        } else {
          cmp = String(valA).toLowerCase().localeCompare(String(valB).toLowerCase())
        }

        return sortDirection.value === 'asc' ? cmp : -cmp
      })
    }

    data.value = displayData.slice(
      (currentPage.value - 1) * 15,
      currentPage.value * 15
    )
  }

  // Sync store state to URL
  function updateURL() {
    const query = { ...route.query }

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

  // Tietojen haku API:sta
  const fetchData = async () => {
    try {
      const res = await axios.get('/api/service/', {
        withCredentials: true
      })
      originalData.value = res.data
      contractData.value = res.data
      searchedData.value = res.data
      numberOfPages.value = Math.max(1, Math.ceil(res.data.length / 15))
      // compute visible slice from data first
      updateVisibleData()
      // initialize page FROM URL
      initializePageFromURL()
    } catch (error) {
      // Error fetching data
    }
  }

  // Päivittää yksittäisen objektin tiedot
  const updateObject = (object) => {
    originalData.value = originalData.value.map(obj =>
      obj.id === object.id ? { ...obj, ...object } : obj
    )
    contractData.value = originalData.value
    searchedData.value = originalData.value
    updateVisibleData()
  }

  const matchesBooleanQuery = (item, query) => {
  
      const fieldAliases = {
        id: 'id',
        tay_number: 'tay_numero',
        tay_numero: 'tay_numero',
        serial_number: 'sarjanumero',
        sarjanumero: 'sarjanumero',
        product_name: ['tuotenimi', 'tuotenimi_en'],
        tuotenimi: ['tuotenimi', 'tuotenimi_en'],
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
  
      const getFieldValues = (obj, field) => {
        const canonical = fieldAliases[field] ?? field
        const keys = Array.isArray(canonical) ? canonical : [canonical]
        return keys.map(key => {
          const v = obj[key]
          return v === undefined || v === null ? '' : String(v).toLowerCase()
        })
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
        (item.tuotenimi_en && item.tuotenimi_en.toLowerCase().includes(lower)) ||
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
          const values = getFieldValues(item, symbol.fieldName.toLowerCase())
          return values.some(v => v.includes(lower))
        }
        return anyFieldIncludes(lower)
      }
  
      const rpn = parseQueryToRpn(query)
      return evaluateRpnBoolean(rpn, item, itemMatchesSingleTerm)
    }

  // Functions for search
  async function searchData(clear) {
    if (clear) {
      searchTerm.value = '';
    }

    currentPage.value = 1

    updateURL()
    await applySearch()
  }

  const applySearch = async () => {
    const searchTermSanitized = searchTerm.value.trim().replace(/\s+/g, " ").toLowerCase(); //Trims whitespaces from beginning and end and replace identifies additinal whitespaces between words

    // Apply search term
    let results = originalData.value;
    if (searchTermSanitized) {
      results = directSearch(originalData.value, searchTermSanitized)
    }
    searchedData.value = results
    numberOfPages.value = Math.ceil(results.length / 15)

    updateVisibleData()
  }

  const directSearch = (candidates, searchTerm) => {
    const hasBooleanOperator = /\b(AND|OR|NOT)\b/i.test(searchTerm) || 
      /\b[A-Za-z_][A-Za-z0-9_]*\s*:/i.test(searchTerm)
    if (hasBooleanOperator) {
        return candidates.filter((item) => matchesBooleanQuery(item, searchTerm))
    } else {
        return candidates.filter(item =>
          Object.values(item).some(value =>
            value && String(value).toLowerCase().includes(searchTerm)
          )
        )
      }
  }

  // Initialize currentPage from route.query preferred
  const initializePageFromURL = async () => {

    searchTerm.value = route.query.search ?? ''

    const p = route.query.page ? parseInt(route.query.page, 10) : 1
    currentPage.value = Number.isNaN(p) ? 1 : p

    isInitialized.value = true
    await applySearch()
    // ensure URL reflects final page state (removes page param when page=1)
    updateURL()
  }

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
  
      // During startup don't push URL (we set it explicitly in initializePageFromURL)
      if (!isInitialized.value) {
        updateVisibleData()
        return
      }
  
      // Update the URL and visible slice whenever page changes after initialization
      updateURL()
      updateVisibleData()
    })

  // Keep URL and visible data in sync when page changes
  watch(() => route.query, async (newQuery) => {
    if (route.path !== '/contracts') return

    searchTerm.value = newQuery.search ?? ''

    const p = newQuery.page ? parseInt(newQuery.page, 10) : 1
    currentPage.value = Number.isNaN(p) ? 1 : p

    await applySearch()
  }, { immediate: false })

  return { 
    data, 
    numberOfPages, 
    currentPage,
    isUrgent,
    isUpcoming,
    isEnding,
    isEnded,
    isUrgentNav,
    isUpcomingNav,
    isEndingNav,
    isEndedNav,
    fetchData,
    updateVisibleData,
    updateObject,
    isMaintenanceDue,
    isMaintenanceUpcoming,
    sortColumn,
    sortDirection,
    searchTerm,
    searchData
  }
})
