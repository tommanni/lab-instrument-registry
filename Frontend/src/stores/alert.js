import { ref } from 'vue'
import { defineStore } from 'pinia'

// alerts for login / adding instruments etc
export const useAlertStore = defineStore('alertStore', () => {
  const alertType = ref(0)
  const visibility = ref(false)
  const alertText = ref(null)
  let timeoutVar

  // displays the alert with the correct type and text
  async function showAlert (type, text) {
    clearTimeout(timeoutVar)
    alertText.value = text
    visibility.value = true
    alertType.value = type
    timeoutVar = setTimeout(() => {
      visibility.value = false
    }, 5000)
  }
  return { alertType, visibility, alertText, showAlert }
  
})
