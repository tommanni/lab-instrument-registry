import { ref } from 'vue'
import { defineStore } from 'pinia'

export const useAlertStore = defineStore('alertStore', () => {
  const alertType = ref(0)
  const visibility = ref(false)
  const alertText = ref(null)
  let timeoutVar

  async function showAlert (type, text) {
    clearTimeout(timeoutVar)
    alertText.value = text
    visibility.value = true
    alertType.value = type
    timeoutVar = setTimeout(() => {
      console.log("testing")
      visibility.value = false
    }, 3000)
  }
  return { alertType, visibility, alertText, showAlert }
  
})
