import { ref } from 'vue'
import { defineStore } from 'pinia'
import axios from 'axios'

export const useUserStore = defineStore('userStore', () => {
  const fullData = ref([])
  const currentData = ref([])
  const currentPage = ref(1)
  const numberOfPages = ref(1)

  const updateVisibleData = () => {
    currentData.value = fullData.value.slice((currentPage.value-1)*15, currentPage.value*15)
  }

  const fetchData = async () => {
    try {
      const res = await axios.get('/api/users/', {
        headers: {
          'Authorization': 'Token ' + document.cookie.split("; ").find((row) => row.startsWith("Authorization="))?.split("=")[1]
        }
      })

      fullData.value = res.data
      currentData.value = res.data.slice(0, 15)
      numberOfPages.value = Math.ceil(res.data.length / 15)
    } catch (error) {
      console.log('Error fetching user data: ', error);
    }
  }

  const deleteUser = async (id) => {
    fullData.value = originalData.value.filter(o => o.id !== id)
    currentData.value = filteredData.value.filter(o => o.id !== id)
    updateVisibleData()
  }

  return { fullData, currentData, currentPage, numberOfPages,
    fetchData, deleteUser, updateVisibleData }
})
