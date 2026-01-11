import { ref, watch } from 'vue'
import { defineStore } from 'pinia'
import axios from 'axios'
import { useI18n } from 'vue-i18n'
import { useRoute, useRouter } from 'vue-router'
import Fuse from 'fuse.js'

import { parseQueryToRpn, evaluateRpnBoolean } from '../searchUtils/index'

export const useDataStore = defineStore('dataStore', () => {
  const { locale } = useI18n()

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
  const DEFAULT_SEARCH_MODE = 'direct'
  const SUPPORTED_SEARCH_MODES = ['direct', 'smart']
  const searchMode = ref(DEFAULT_SEARCH_MODE)
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
        const valA = (a[sortColumn.value.toLowerCase()] ?? '').toString().toLowerCase()
        const valB = (b[sortColumn.value.toLowerCase()] ?? '').toString().toLowerCase()

        const isEmptyA = valA === null || valA === '' || valA === undefined
        const isEmptyB = valB === null || valB === '' || valB === undefined

        // Put empty values last
        if (isEmptyA && !isEmptyB) return 1
        if (!isEmptyA && isEmptyB) return -1
        if (isEmptyA && isEmptyB) return 0

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

    const anyFieldIncludes = (lower) => Object.values(item).some(value => {
      return value !== null && value !== undefined &&
             value.toString().toLowerCase().includes(lower);
    });

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

  const updateDuplicateTuotenimiEN = (fiName, newEn) => {
    const normalized = (fiName || '').trim().toLowerCase()
    const updateList = (list) =>
      list.map(obj =>
        (obj.tuotenimi || '').trim().toLowerCase() === normalized
          ? { ...obj, tuotenimi_en: newEn }
          : obj
      )

    originalData.value = updateList(originalData.value)
    filteredData.value = updateList(filteredData.value)
    searchedData.value = updateList(searchedData.value)
    data.value = updateList(data.value)
  }


  const addObject = (object) => {
    originalData.value.push(object)
    updateVisibleData()
  }

  const filterData = async () => {

    currentPage.value = 1

    updateURL()
    await applySearchAndFilter()

  }

  async function searchData(clear) {
    if (clear) {
      searchTerm.value = '';
    }

    currentPage.value = 1

    updateURL()
    await applySearchAndFilter()
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

    if (searchMode.value && searchMode.value !== DEFAULT_SEARCH_MODE) {
      query.search_mode = searchMode.value
    } else {
      delete query.search_mode
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

  const applySearchAndFilter = async () => {
    const searchTermSanitized = searchTerm.value.trim().replace(/\s+/g, " ").toLowerCase(); //Trims whitespaces from beginning and end and replace identifies additinal whitespaces between words

    // Apply filters
    const fv = filterValues.value
    const filtered = originalData.value.filter(item =>
      (!fv.yksikko || item.yksikko === fv.yksikko) &&
      (!fv.huone || item.huone == fv.huone) &&
      (!fv.vastuuhenkilo || item.vastuuhenkilo == fv.vastuuhenkilo) &&
      (!fv.tilanne || item.tilanne === fv.tilanne)
    )
    filteredData.value = filtered

    // Apply search term
    let results = filtered
    if (searchTermSanitized) {
      switch(searchMode.value) {
        case 'direct':
          results = directSearch(filtered, searchTermSanitized)
          break
        case 'smart':
          results = await smartSearch(filtered, searchTermSanitized)
          break
      }
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

  const smartSearch = async (candidates, searchTerm) => {
    const fuzzyResults = fuzzySearch(candidates, searchTerm)

    if (!(fuzzyResults.length > 0)) {
      const semanticResults = await semanticSearch(searchTerm)
      const allowed = new Map(candidates.map(item => [item.id, item]))
      const combined = [...fuzzyResults]
      semanticResults.forEach(result => {
        const candidate = allowed.get(result.id)
        if (candidate) {
          combined.push(candidate)
        }
      })
      return [...new Map(combined.map(item => [item.id, item])).values()]
    }

    return fuzzyResults
  }

  const fuzzySearch = (candidates, searchTerm) => {
    const fuseOptions = {
      keys: [
        { name: 'tuotenimi', weight: 5 },
        { name: 'tuotenimi_en', weight: 5 },
        { name: 'merkki_ja_malli', weight: 3 },
        { name: 'tay_numero', weight: 4 },
        { name: 'sarjanumero', weight: 3},
        { name: 'vastuuhenkilo', weight: 1},
        { name: 'tilanne', weight: 1 },
        { name: 'vanha_sijainti', weight: 0.8 },
        { name: 'toimittaja', weight: 0.8 },
        { name: 'yksikko', weight: 0.8 },
        { name: 'kampus', weight: 0.5 },
        { name: 'rakennus', weight: 0.5 },
        { name: 'huone', weight: 0.5 },
        { name: 'lisatieto', weight: 0.2 },
      ],
        threshold: 0.2, // 0.0 exact match, 1.0 loose match
        findAllMatches: true,
        minMatchCharLength: 3,
        shouldSort: true,
        ignoreLocation: true,
        includeMatches: true,
    };

    const fuse = new Fuse(candidates, fuseOptions)
    const fuseResults = fuse.search(searchTerm)

    return fuseResults.map(r => r.item)
  }

  const semanticSearch = async (searchTerm) => {
    try {
      // Semantic search with filters
      const semanticRes = await axios.get('/api/instruments/search/', {
        params: { q: searchTerm },
        withCredentials: true
      })
      const results = semanticRes.data
      return results
    } catch (error) {
      console.error("Error during semantic search fallback:", error)
      return []
    }
  }

  // Function for data initialization based on active filters
  const initializePageFromURL = async () => {

    Object.keys(filterValues.value).forEach((key)  => {
      filterValues.value[key] = route.query[key] ?? null
    });

    searchTerm.value = route.query.search ?? ''
    const queryMode = String(route.query.search_mode || '').toLowerCase()
    searchMode.value = SUPPORTED_SEARCH_MODES.includes(queryMode) ? queryMode : DEFAULT_SEARCH_MODE

    const p = route.query.page ? parseInt(route.query.page, 10) : 1
    currentPage.value = Number.isNaN(p) ? 1 : p

    await applySearchAndFilter()
  }

  // Watcher for filter/search/pagination changes
  watch(() => route.query, async (newQuery) => {
    if (route.path !== '/') return

    Object.keys(filterValues.value).forEach(key => {
      filterValues.value[key] = newQuery[key] ?? null
    })

    searchTerm.value = newQuery.search ?? ''
    const queryMode = String(newQuery.search_mode || '').toLowerCase()
    searchMode.value = SUPPORTED_SEARCH_MODES.includes(queryMode) ? queryMode : DEFAULT_SEARCH_MODE

    const p = newQuery.page ? parseInt(newQuery.page, 10) : 1
    currentPage.value = Number.isNaN(p) ? 1 : p

    await applySearchAndFilter()

  }, {immediate: false})

  watch(searchMode, (mode) => {
    if (!SUPPORTED_SEARCH_MODES.includes(mode)) {
      searchMode.value = DEFAULT_SEARCH_MODE
      return
    }
    updateURL()
  })

  return {
    data,
    originalData,
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
    searchMode,
    initializePageFromURL,
    locale,
    updateDuplicateTuotenimiEN
  }
})
