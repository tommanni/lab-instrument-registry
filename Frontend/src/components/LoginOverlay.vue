<script setup>
import { ref } from 'vue'
import { useI18n } from 'vue-i18n'
import axios from 'axios'  // Bring axios
import { useDataStore } from '@/stores/data'
import { useAlertStore } from "@/stores/alert.js";

const { t } = useI18n()

const showOverlay = ref(false)
const email = ref('')      // Define email
const password = ref('')   // Define password
const store = useDataStore()
const alertStore = useAlertStore()

const loginUser = async () => {
  try {
    // API-call for login
    const response = await axios.post('/api/login/', {
      email: email.value,
      password: password.value
    });
    // Set cookie that saves token. Should work for 2h
    const expiryDate = new Date(response.data.expiry).toUTCString();
    // TODO add commented parameters to cookie definition for live build HTTPS
    document.cookie = 'Authorization=' + response.data.token + '; Expires=' + expiryDate + '; path=/' /*; Secure; SameSite=Strict'; */
    store.isLoggedIn = true
    email.value = ''
    password.value = ''
    closeOverlay();
    // todo users name in the welcome msg (not critical)
    alertStore.showAlert(0, `${t('message.sisaan_kirjauduttu')}`)
    closeOverlay()
  } catch (error) {
    console.error('Kirjautumisvirhe:', error)

    // display an appropriate error message if possible
    if (error.response.data.detail != undefined) {
      alertStore.showAlert(1, `${t('message.kirjautumisvirhe')} ${t('message.virhe')}: ${error.response.data.detail}`)
    } else {
      alertStore.showAlert(1, `${t('message.kirjautumisvirhe')}: ${t('message.tuntematon_virhe')}`)
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
  <div class="login-btn">
    <!-- Login button to open overlay -->
    <button v-if="!store.isLoggedIn" class="login-button" @click="openOverlay">{{ t('message.kirjaudu_painike') }}</button>

    <!-- Overlay only shows when showOverlay = True -->
    <div v-if="showOverlay" class="overlay-backdrop">
      <div class="overlay-content">
        <!-- X-button in top right corner -->
        <button class="close-button" @click="closeOverlay">×</button>
        <h3>{{ t('message.kirjaudu') }}</h3>
        <p></p>
        <form @submit.prevent="loginUser">
          <!-- Email input -->
          <div data-mdb-input-init class="form-outline mb-4">
            <label class="form-label" for="login-email">{{ t('message.sahkoposti') }}</label>
            <input
              v-model="email"
              type="email"
              id="login-email"
              name="email"
              autocomplete="email"
              class="form-control"
              required
            />
          </div>

          <!-- Password input -->
          <div data-mdb-input-init class="form-outline mb-4">
            <label class="form-label" for="login-password">{{ t('message.salasana') }}</label>
            <input
              v-model="password"
              type="password"
              id="login-password"
              name="password"
              autocomplete="current-password"
              class="form-control"
              required
            />
          </div>

          <!-- Submit button -->
          <button type="submit" data-mdb-button-init data-mdb-ripple-init class="signin-button">
            {{ t('message.kirjaudu_painike') }}
          </button>
        </form>
      </div>
      <br/>
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
  z-index: 1031;
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

.login-button {
  padding: 5px 10px;
  margin-left: 5px;
  margin-right: 20px;
  background-color: #cf286f;
  color: white;
  border: none;
  cursor: pointer;
  border-radius: 5px;
  text-align: center;
  white-space: nowrap;
}

.login-button:hover {
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
