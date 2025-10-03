import { ref, computed, watch } from 'vue'
import { defineStore } from 'pinia'
import axios from 'axios'

export const useContractStore = defineStore('contractStore', () => {
  // Alkuperäinen data haetaan API:sta
  const originalData = ref([])
  // Kaikki haetut tiedot
  const contractData = ref([])
  // Näytettävä data (sivuittain)
  const data = ref([])

  // Sivunumeroiden hallinta
  const currentPage = ref(1)

  // Lasketaan sivujen määrä 
  // Jos dataa ei ole, palautetaan vähintään 1.
  const numberOfPages = computed(() => {
    const totalCount = contractData.value.length;
    console.log("Tietueiden määrä: ", totalCount);
    const pages = Math.ceil(totalCount / 15);
    return pages > 0 ? pages : 1;
  })

  // Päivitetään näkyvä data käyttäen suodatettua ja lajiteltua dataa.
  const updateVisibleData = () => {
    data.value = contractData.value.slice(
      (currentPage.value - 1) * 15,
      currentPage.value * 15
    )
    console.log('Päivitetty näkyvä data:', data.value);
  }

  // Watcher: jos filteredSortedData muuttuu, nollataan sivunumero ja päivitetään visible data.
  watch([contractData, currentPage], updateVisibleData, { immediate: true })

  // Tietojen haku API:sta
  const fetchData = async () => {
    try {
      const res = await axios.get('/api/service/', {
        withCredentials: true
      })
      console.log('Haettu data:', res.data)
      originalData.value = res.data
      contractData.value = res.data
      currentPage.value = 1  // Nollataan sivunumero
      updateVisibleData()
    } catch (error) {
      console.log('Error fetching data: ', error)
    }
  }

  // Päivittää yksittäisen objektin tiedot
  const updateObject = (object) => {
    originalData.value = originalData.value.map(obj =>
      obj.id === object.id ? { ...obj, ...object } : obj
    )
    updateVisibleData()
  }

  // Lisää uuden objektin
  const addObject = (object) => {
    originalData.value.push(object)
    updateVisibleData()
  }

  return { 
    data, 
    numberOfPages, 
    currentPage, 
    fetchData, 
    updateVisibleData, 
    updateObject, 
    addObject,
    //filteredSortedData
  }
})
