<script setup>
import { ref } from 'vue'
import { useI18n } from 'vue-i18n'
import axios from 'axios'
import { useDataStore } from '@/stores/data'
import { useAlertStore } from '@/stores/alert'

const { t } = useI18n()

const showOverlay = ref(false)
const store = useDataStore()
const alertStore = useAlertStore()

const openOverlay = () => {
    showOverlay.value = true
}

const closeOverlay = () => {
    showOverlay.value = false
}

const logoutUser = async () => {
    try {
        // API-call for logout
        const response = await axios.post('/api/logout/', {}, {
          withCredentials: true
        });
        store.isLoggedIn = false
        closeOverlay();
        // Show success alert
        alertStore.showAlert(0, t('message.ulos_kirjauduttu'))
    } catch (error) {
        // Error logging out
    }
}

</script>

<template>
  <div class="logout-btn">
    <!-- Logout button to open overlay -->
    <button v-if="store.isLoggedIn" class="logout-button" @click="openOverlay">{{ t('message.kirjaudu_ulos_painike') }}</button>

    <!-- Overlay only shows when showOverlay = True -->
    <div v-if="showOverlay" class="overlay-backdrop">
      <div class="overlay-content">
        <h3>{{ t('message.kirjaudu_ulos') }}</h3>
        <p></p>
        
        <div class="button-row">
            <button @click="logoutUser" class="confirm-button">
                {{ t('message.kyllä_vastaus') }}
            </button>
            <button @click="closeOverlay" class="cancel-button">
                {{ t('message.ei_vastaus') }}
            </button>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
/* Half seethrough background for overlay */
.overlay-backdrop {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background-color: rgba(0, 0, 0, 0.5);
  z-index: 1060;
}

/* Centered content for overlay */
.overlay-content {
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  background: #fff;
  padding: 2em;
  border-radius: 4px;
  box-shadow: 0 2px 10px rgba(0, 0, 0, 0.3);
}

.logout-button {
  padding: 5px 10px;
  margin-left: 5px;
  margin-right: 0px;
  background-color: #cf286f;
  color: white;
  border: none;
  cursor: pointer;
  border-radius: 5px;
  text-align: center;
  white-space: nowrap;
}

.logout-button:hover {
  background-color: #F5A5C8;
}

.confirm-button {
  padding: 5px 10px;
  margin-left: 10px;
  background-color: #4E008E;
  color: white;
  border: none;
  cursor: pointer;
  border-radius: 5px;
  text-align: center;
  white-space: nowrap;
}

.confirm-button:hover {
  background-color: #ab9bcb;
}

.cancel-button {
  padding: 5px 10px;
  margin-left: 10px;
  background-color: #4E008E;
  color: white;
  border: none;
  cursor: pointer;
  border-radius: 5px;
  text-align: center;
  white-space: nowrap;
}

.cancel-button:hover {
  background-color: #ab9bcb;
}

</style>