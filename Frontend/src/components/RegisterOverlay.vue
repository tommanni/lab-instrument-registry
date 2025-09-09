<script setup>
import { ref } from 'vue'
import { useI18n } from 'vue-i18n'
import axios from 'axios'
import { useDataStore } from '@/stores/data'

const { t } = useI18n()

const showOverlay = ref(false)
const email = ref('')
const password = ref('')
const invite_code = ref('')
const full_name = ref('')
const store = useDataStore()
const registerUser = async () => {
  try {
    // API-kutsu kirjautumiseen
    const response = await axios.post('/api/register/', {
      email: email.value,
      password: password.value,
      invite_code: invite_code.value,
      full_name: full_name.value
    })
    // Joku validaatio joskus pliis et kirjautuko vai ei :)
    email.value = ''
    password.value = ''
    invite_code.value = ''
    full_name.value = ''
    closeOverlay()
  } catch (error) {
    console.error('Kirjautumisvirhe:', error)
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
    <button v-if="!store.isLoggedIn" class="register-button" @click="openOverlay">{{ t('message.register_painike') }}</button>

    <!-- Overlay näkyy vain, kun showOverlay on true -->
    <div v-if="showOverlay" class="overlay-backdrop">
      <div class="overlay-content">
        <!-- X-painike oikeassa yläkulmassa -->
        <button class="close-button" @click="closeOverlay">×</button>
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
          <button type="submit" data-mdb-button-init data-mdb-ripple-init class="signin-button">
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
  z-index: 1031;
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

.register-button {
  padding: 5px 10px;
  margin-left: 10px;
  margin-right: 5px;
  background-color: #cf286f;
  color: white;
  border: none;
  cursor: pointer;
  border-radius: 5px;
  text-align: center;
  white-space: nowrap;
}

.register-button:hover {
  background-color: #F5A5C8;
}

.close-button {
  position: absolute;
  top: 0.5em;
  right: 0.5em;
  background: transparent;
  border: none;
  font-size: 1.4rem;
  cursor: pointer;
  line-height: 1;
}

.close-button:hover {
  color: #b00;
}

.signin-button {
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

.signin-button:hover {
  background-color: #ab9bcb;
}
</style>
