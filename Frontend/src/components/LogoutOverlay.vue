<script setup>
import { ref } from 'vue'
import { useI18n } from 'vue-i18n'
import axios from 'axios'
import { useDataStore } from '@/stores/data'
import { useAlertStore } from '@/stores/alert'
import { useMediaQuery } from '@vueuse/core'

const { t } = useI18n();
const isMobile = useMediaQuery('(max-width: 768px');

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
  <div>
    <!-- Logout button to open overlay -->
     <div v-if="store.isLoggedIn">
        <button v-if="isMobile" class="btn btn-outline-primary fs-4 d-flex" @click="openOverlay"><i class="bi bi-box-arrow-right"></i></button>
        <button v-else class="btn btn-primary" @click="openOverlay">{{ t('message.kirjaudu_ulos_painike') }}</button>
     </div>
    

    <!-- Overlay only shows when showOverlay = True -->
    <div v-if="showOverlay" class="overlay-backdrop">
      <div class="overlay-content">
        <h3>{{ t('message.kirjaudu_ulos') }}</h3>
        <p></p>

        <div class="modal-footer justify-content-center gap-2">
            <button @click="logoutUser" class="btn btn-primary">
                {{ t('message.kylla_vastaus') }}
            </button>
            <button @click="closeOverlay" class="btn btn-secondary">
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


</style>