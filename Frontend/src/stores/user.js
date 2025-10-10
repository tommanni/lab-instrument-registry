import { ref } from 'vue'
import { defineStore } from 'pinia'
import axios from 'axios'
import { useDataStore } from '@/stores/data';

export const useUserStore = defineStore('userStore', () => {
  const fullData = ref([])
  const currentData = ref([])
  const currentPage = ref(1)
  const numberOfPages = ref(1)
  const user = ref(null)
  const dataStore = useDataStore()

  const updateVisibleData = () => {
    currentData.value = fullData.value.slice((currentPage.value-1)*15, currentPage.value*15)
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
      user.value = ref(null)
      return
    }
    // Fetch current user data
    try {
      const res = await axios.get(`/api/users/${'me'}/`, { 
        withCredentials: true
      })
      user.value = res.data
    } catch (error) {
      user.value = ref(null)
    }
  }

  const deleteUser = async (id) => {
    fullData.value = originalData.value.filter(o => o.id !== id)
    currentData.value = filteredData.value.filter(o => o.id !== id)
    updateVisibleData()
  }

  return { fullData, currentData, currentPage, numberOfPages, user,
    fetchData, deleteUser, updateVisibleData, fetchUser }
})
