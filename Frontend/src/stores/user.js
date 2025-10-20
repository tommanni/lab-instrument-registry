import { ref, watch } from 'vue'
import { defineStore } from 'pinia'
import axios from 'axios'
import { useRoute, useRouter } from 'vue-router'
import { useDataStore } from '@/stores/data';

export const useUserStore = defineStore('userStore', () => {
  const route = useRoute()
  const router = useRouter()
  const fullData = ref([])
  const searchedData = ref([])
  const currentData = ref([])
  const currentPage = ref(1)
  const numberOfPages = ref(1)
  const sortColumn = ref('')
  const sortDirection = ref('none')
  const user = ref(null)
  const dataStore = useDataStore()
  const searchTerm = ref('')

  const updateVisibleData = () => {
    // Make copy of searched data to sort and paginate
    let displayData = [...(searchedData.value || [])]
    
    // If sorting is applied, sort the data first
    if (sortColumn.value && sortDirection.value !== 'none') {
      displayData.sort((a, b) => {
        const valA = (a[sortColumn.value.toLowerCase()] || '').toString().toLowerCase()
        const valB = (b[sortColumn.value.toLowerCase()] || '').toString().toLowerCase()
        const comp = valA.localeCompare(valB)
        return sortDirection.value === 'asc' ? comp : -comp
      })
    }

    numberOfPages.value = Math.max(1, Math.ceil(displayData.length / 15))
    // Clamp currentPage
    if (currentPage.value < 1) currentPage.value = 1
    if (currentPage.value > numberOfPages.value) currentPage.value = numberOfPages.value
    // Paginate the data
    currentData.value = displayData.slice((currentPage.value - 1) * 15, currentPage.value * 15)
  }
  
  // Sync store state to URL and sessionStorage
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

  const fetchData = async () => {
    try {
      const res = await axios.get('/api/users/', {
        withCredentials: true
      })

      fullData.value = res.data
      currentData.value = res.data.slice(0, 15)
      numberOfPages.value = Math.ceil(res.data.length / 15)
    } catch (error) {
      // Error fetching user data
    }
  }

  const fetchUser = async () => {
    // If not logged in, set user to null
    if (!dataStore.isLoggedIn) {
      user.value = null
      return
    }
    // Fetch current user data
    try {
      const res = await axios.get(`/api/users/me/`, { 
        withCredentials: true
      })
      user.value = res.data
    } catch (error) {
      user.value = null
    }
  }

  const deleteUser = async (id) => {
    fullData.value = originalData.value.filter(o => o.id !== id)
    currentData.value = filteredData.value.filter(o => o.id !== id)
    updateVisibleData()
  }

  const searchData = (clear) => {
    if (clear) {
      searchTerm.value = '';
    }
    
    currentPage.value = 1

    // update URL / sessionStorage
    updateURL()

    // Filter data based on search term
    const lowerSearch = searchTerm.value.toLowerCase()
    if (lowerSearch) {
      searchedData.value = fullData.value.filter(user => 
        user.full_name.toLowerCase().includes(lowerSearch) || 
        user.email.toLowerCase().includes(lowerSearch)
      )
    } else {
      searchedData.value = fullData.value
    }

    updateVisibleData()
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

    // Use shared updater to keep behavior consistent and persist state
    updateURL()
    updateVisibleData()
  })

  watch(() => route.query, (newQuery) => {
      if (route.path !== '/admin/users') return

      searchTerm.value = newQuery.search ?? ''
      const p = newQuery.page ? parseInt(newQuery.page, 10) : 1
      currentPage.value = Number.isNaN(p) ? 1 : p

      searchData()
      updateVisibleData()
  }, { immediate: false })

  return { fullData, currentData, currentPage, numberOfPages, user,
    fetchData, deleteUser, updateVisibleData, fetchUser, searchData, searchTerm }
})
