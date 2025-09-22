<script setup>
import { ref } from 'vue'
import { useI18n } from 'vue-i18n'
import axios from 'axios'  // Bring axios
import { useDataStore } from '@/stores/data'

const { t } = useI18n()

const showOverlay = ref(false)
const email = ref('')      // Define email
const password = ref('')   // Define password
const store = useDataStore()
const loginUser = async () => {
  try {
    // API-call for login
    const response = await axios.post('/api/login/', {
      email: email.value,
      password: password.value
    });
    console.log('Kirjautuminen onnistui:', response.data);
    // Set cookie that saves token. Expiry shows in devTools as "Session", but should work for 2h
    document.cookie = 'Authorization='+response.data.token+'; Expires='+response.data.expiry+'; path=/'
    store.isLoggedIn = true
    email.value = ''
    password.value = ''
    closeOverlay();
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
            <label class="form-label" for="form2Example1">{{ t('message.sahkoposti') }}</label>
            <input v-model="email" type="email" id="form2Example1" class="form-control" />
          </div>

          <!-- Password input -->
          <div data-mdb-input-init class="form-outline mb-4">
            <label class="form-label" for="form2Example2">{{ t('message.salasana') }}</label>
            <input v-model="password" type="password" id="form2Example2" class="form-control" /> 
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
