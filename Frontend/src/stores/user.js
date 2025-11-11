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
        let valA = a[sortColumn.value]
        let valB = b[sortColumn.value]

        // Handle boolean values
        if (typeof valA === 'boolean' && typeof valB === 'boolean') {
          return sortDirection.value === 'asc' ? valB - valA : valA - valB
        }

        valA = (valA ?? '').toString().toLowerCase()
        valB = (valB ?? '').toString().toLowerCase()

        const comp = valA.localeCompare(valB)
        return sortDirection.value === 'asc' ? comp : -comp
      });
    }

    // Paginate the data
    numberOfPages.value = Math.max(1, Math.ceil(displayData.length / 15))

    // Clamp currentPage if it’s too high (e.g., after a new search)
    if (currentPage.value > numberOfPages.value) {
      currentPage.value = numberOfPages.value
    }

    currentData.value = displayData.slice((currentPage.value - 1) * 15, currentPage.value * 15)
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

  const fetchData = async () => {
    try {
      const res = await axios.get('/api/users/', {
        withCredentials: true
      })

      fullData.value = res.data
      searchedData.value = res.data;
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
    fullData.value = fullData.value.filter(o => o.id !== id)
    currentData.value = searchedData.value.filter(o => o.id !== id)
    updateVisibleData()
  }

  const searchData = (clear) => {
    if (clear) {
      searchTerm.value = '';
    }
    
    // update URL
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

  // Keep URL and visible data in sync when page changes
  watch(() => route.query, (newQuery) => {
      if (route.path !== '/admin/users') return

      searchTerm.value = newQuery.search ?? ''
      const p = newQuery.page ? parseInt(newQuery.page, 10) : 1
      currentPage.value = Number.isNaN(p) ? 1 : p

      searchData()
      updateVisibleData()
  }, { immediate: true })

  return { fullData, currentData, currentPage, numberOfPages, user, sortColumn, sortDirection,
    fetchData, deleteUser, updateVisibleData, fetchUser, searchData, searchTerm }
})
