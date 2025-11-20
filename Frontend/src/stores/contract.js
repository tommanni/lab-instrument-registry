import { ref, computed, watch } from 'vue'
import { defineStore } from 'pinia'
import { useRoute, useRouter } from 'vue-router'
import axios from 'axios'

export const useContractStore = defineStore('contractStore', () => {
  // Alkuperäinen data haetaan API:sta
  const originalData = ref([])
  // Kaikki haetut tiedot
  const contractData = ref([])
  // Näytettävä data (sivuittain)
  const data = ref([])

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
    (contractData.value || []).filter(item => isMaintenanceDue(item.seuraava_huolto)).length
  )
  const isUpcoming = computed(() =>
    (contractData.value || []).filter(item => isMaintenanceUpcoming(item.seuraava_huolto)).length
  )
  const isEnding = computed(() => 
  (contractData.value || []).filter(item => isMaintenanceUpcoming(item.huoltosopimus_loppuu)).length
  )
  const isEnded = computed(() => 
  (contractData.value || []).filter(item => isMaintenanceDue(item.huoltosopimus_loppuu)).length
  )

  // Päivitetään näkyvä data käyttäen suodatettua ja lajiteltua dataa.
  const updateVisibleData = () => {
    // Make copy of searched data to sort and paginate
    let displayData = [...(contractData.value || [])]

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
    updateVisibleData()
  }

  // Lisää uuden objektin
  const addObject = (object) => {
    originalData.value.push(object)
    updateVisibleData()
  }

  // Initialize currentPage from route.query preferred
  function initializePageFromURL() {
    const hasQueryPage = typeof route.query.page !== 'undefined'

    if (hasQueryPage) {
      const p = route.query.page ? parseInt(route.query.page, 10) : 1
      currentPage.value = Number.isNaN(p) ? 1 : p
    }

    // clamp to available pages
    if (currentPage.value < 1) currentPage.value = 1
    if (numberOfPages.value && currentPage.value > numberOfPages.value) currentPage.value = numberOfPages.value

    updateVisibleData()
    // allow watcher to update URL from now on
    isInitialized.value = true
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
  watch(() => route.query, (newQuery) => {
      if (route.path !== '/contracts') return

      const p = newQuery.page ? parseInt(newQuery.page, 10) : 1
      currentPage.value = Number.isNaN(p) ? 1 : p

      updateVisibleData()
  }, { immediate: false })

  return { 
    data, 
    numberOfPages, 
    currentPage,
    isUrgent,
    isUpcoming,
    isEnding,
    isEnded,
    fetchData, 
    updateVisibleData, 
    updateObject, 
    addObject,
    isMaintenanceDue,
    isMaintenanceUpcoming,
    sortColumn,
    sortDirection
    //filteredSortedData
  }
})
