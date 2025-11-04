<script setup>
import { ref } from 'vue'
import { useI18n } from 'vue-i18n'
import axios from 'axios'
import { useDataStore } from '@/stores/data'
import { useAlertStore } from '@/stores/alert'

const { t } = useI18n()

const showOverlay = ref(false)
const email = ref('')
const password = ref('')
const invite_code = ref('')
const full_name = ref('')
const store = useDataStore()
const alertStore = useAlertStore()

const registerUser = async () => {
  try {
    // API-kutsu kirjautumiseen
    // API call to sign in
    const response = await axios.post('/api/register/', {
      email: email.value,
      password: password.value,
      invite_code: invite_code.value,
      full_name: full_name.value
    }, {
      withCredentials: true
    })
    email.value = ''
    password.value = ''
    invite_code.value = ''
    full_name.value = ''
    alertStore.showAlert(0, `${t('message.rekisteroity')}`)
    closeOverlay()
  } catch (error) {
        if (error.response && error.response.data && error.response.data.message) {
            alertStore.showAlert(1, t('message.virhe') + error.response.data.message);
        }
        else {
            alertStore.showAlert(1, t('message.rekisteroimisvirhe'));
        }
  }
}

const openOverlay = () => {
  showOverlay.value = true
}

const closeOverlay = () => {
  showOverlay.value = false
}
</script>

<template>
  <div class="register-btn">
    <!-- Avausnappi -->
    <button v-if="!store.isLoggedIn" class="btn btn-primary ms-2" @click="openOverlay">{{ t('message.register_painike') }}</button>

    <!-- Overlay näkyy vain, kun showOverlay on true -->
    <div v-if="showOverlay" class="overlay-backdrop">
      <div class="overlay-content">
        <!-- X-painike oikeassa yläkulmassa -->
        <button type="button" class="btn-close position-absolute top-0 end-0 m-3" @click="closeOverlay" aria-label="Close"></button>
        <h3>{{ t('message.register_painike') }}</h3>
        <p></p>
        <form @submit.prevent="registerUser">
          <div data-mdb-input-init class="form-outline mb-4">
            <label class="form-label" for="form2Example2">{{ t('message.koodi') }}</label>
            <input v-model="invite_code" type="text" id="form3Example2" class="form-control" /> 
          </div>
          <!-- Email input -->
          <div data-mdb-input-init class="form-outline mb-4">
            <label class="form-label" for="form2Example1">{{ t('message.sahkoposti') }}</label>
            <input v-model="email" type="email" id="form3Example1" class="form-control" />
          </div>
          
          <div data-mdb-input-init class="form-outline mb-4">
            <label class="form-label" for="form2Example2">{{ t('message.koko_nimi') }}</label>
            <input v-model="full_name" type="text" id="form3Example3" class="form-control" /> 
          </div>

          <div data-mdb-input-init class="form-outline mb-4">
            <label class="form-label" for="form2Example2">{{ t('message.salasana') }}</label>
            <input v-model="password" type="password" id="form3Example4" class="form-control" /> 
          </div>

          <!-- Submit button -->
          <button type="submit" data-mdb-button-init data-mdb-ripple-init class="btn btn-primary ms-2">
            {{ t('message.register_painike') }}
          </button>
        </form>
      </div>
      <br/>
    </div>
  </div>
</template>

<style scoped>
/* Puoliläpinäkyvä tausta overlaylle */
.overlay-backdrop {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background-color: rgba(0, 0, 0, 0.5);
  z-index: 1060;
}

/* Keskitetty sisältö overlayn sisällä */
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
