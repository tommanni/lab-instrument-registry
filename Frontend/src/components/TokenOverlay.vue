<script setup>
import { useAlertStore } from '@/stores/alert';
import axios from 'axios'
import { ref } from 'vue'
import { useI18n } from 'vue-i18n'
import { useUserStore } from '@/stores/user'

const alertStore = useAlertStore()
const { t } = useI18n()
const showOverlay = ref(false)
const userStore = useUserStore()
const token = ref("")

const openOverlay = () => {
  showOverlay.value = true
}

const closeOverlay = () => {
  showOverlay.value = false
}

const generateToken = async() => {
  try {
    const res = await axios.get('/api/invite/', {
      withCredentials: true
    })
    token.value = res.data.invite_code
  } catch (error) {
    alertStore.showAlert(1, `${t('message.kutsukoodi_virhe')}`)
  }
}
</script>

<template>
  <div>
    <!-- Avausnappi -->
    <button class="login-button" @click="openOverlay">{{ t('message.luo_kayttajakoodi') }}</button>

    <!-- Overlay näkyy vain, kun showOverlay on true -->
    <div v-if="showOverlay" class="overlay-backdrop">
      <div class="overlay-content">
        <!-- X-painike oikeassa yläkulmassa -->
        <h3>{{ t('message.kayttajakoodin_luonti') }}</h3>
        <button class="signin-button" @click="generateToken">{{ t('message.luo_uusi_kayttajakoodi') }}</button>
        <p></p>
        <button class="close-button" @click="closeOverlay">×</button>
        <h4>{{ t('message.luotu_kayttajakoodi') }}</h4>
        <h5 class="code-label">{{ token }}</h5>
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

.login-button {
  padding: 5px 10px;
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
  margin-top: 10px;
  margin-bottom: 10px;
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
