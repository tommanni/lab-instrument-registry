import { ref } from 'vue'
import { defineStore } from 'pinia'
import axios from 'axios'

export const useDataStore = defineStore('dataStore', () => {
  const originalData = ref([])
  const data = ref([])
  const filteredData = ref([])
  const searchedData = ref([])
  const currentPage = ref(1)
  const numberOfPages = ref(1)
  const isLoggedIn = ref(false)
  const sortColumn = ref('')
  const sortDirection = ref('none')
 
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

  const fetchData = async () => {
    try {
      const res = await axios.get('/api/instruments/')
      originalData.value = res.data
      data.value = res.data.slice(0, 15)
      numberOfPages.value = Math.ceil(res.data.length / 15)
      searchedData.value = res.data
      filteredData.value = res.data
    } catch (error) {
      console.log('Error fetching data: ', error);
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
    filteredData.value = originalData.value.filter(item => {
    let match = true
    if (yksikko) {
    match = match && item.yksikko === yksikko
     }
    if (huone) {
    match = match && item.huone === huone
     }
    if (vastuuhenkilo) {
    match = match && item.vastuuhenkilo === vastuuhenkilo
     }
    if (tilanne) {
    match = match && item.tilanne === tilanne
     }
    return match
     })
    searchedData.value = filteredData.value
    currentPage.value = 1
    numberOfPages.value = Math.ceil(searchedData.value.length / 15)
    updateVisibleData()
     }

  const searchData = (searchTerm) => {
    if (!searchTerm) {
      searchedData.value = [...filteredData.value]
      currentPage.value = 1
      numberOfPages.value = Math.ceil(searchedData.value.length / 15)
      updateVisibleData()
      return
    }

    const results = filteredData.value.filter((item) => {
      const lowerSearchTerm = searchTerm.toLowerCase()
      
      // Etsi kaikista mahdollisista nimikentistä
      return (
        (item.id.toString().includes(lowerSearchTerm)) ||
        (item.tay_numero &&
          item.tay_numero.toLowerCase().includes(lowerSearchTerm)) ||
        (item.sarjanumero &&
          item.sarjanumero.toLowerCase().includes(lowerSearchTerm)) ||
        (item.toimituspvm &&
          item.toimituspvm.toString().toLowerCase().includes(lowerSearchTerm)) ||
        (item.toimittaja &&
          item.toimittaja.toLowerCase().includes(lowerSearchTerm)) ||
        (item.lisatieto &&
          item.lisatieto.toLowerCase().includes(lowerSearchTerm)) ||
        (item.vanha_sijainti &&
          item.vanha_sijainti.toLowerCase().includes(lowerSearchTerm)) ||
        (item.tuotenimi && 
         item.tuotenimi.toLowerCase().includes(lowerSearchTerm)) ||
        (item.merkki_ja_malli && 
         item.merkki_ja_malli.toLowerCase().includes(lowerSearchTerm)) ||
        (item.yksikko && 
         item.yksikko.toLowerCase().includes(lowerSearchTerm)) ||
        (item.kampus && 
         item.kampus.toLowerCase().includes(lowerSearchTerm)) ||
        (item.rakennus && 
         item.rakennus.toLowerCase().includes(lowerSearchTerm)) ||
        (item.huone && 
         item.huone.toLowerCase().includes(lowerSearchTerm)) ||
        (item.vastuuhenkilo && 
         item.vastuuhenkilo.toLowerCase().includes(lowerSearchTerm)) ||
        (item.tilanne && 
         item.tilanne.toLowerCase().includes(lowerSearchTerm))
      )
    })

    searchedData.value = results

    currentPage.value = 1
    numberOfPages.value = Math.ceil(searchedData.value.length / 15)
    updateVisibleData()
  
  }

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
    sortDirection  
  }
})
