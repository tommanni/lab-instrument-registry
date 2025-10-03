<script setup>
import Navigation from './components/Navigation.vue';
import { RouterView } from 'vue-router';
import TuniFooter from './components/Footer.vue';
import Alert from './components/Alert.vue';
import { onMounted } from 'vue';
import { useDataStore } from '@/stores/data';
import axios from 'axios';
import { useI18n } from 'vue-i18n';

const { t, locale } = useI18n()

const dataStore = useDataStore()

// These should have their own file later on?
function getCookie(name) {
  const cookies = document.cookie.split(';');
  for (const cookie of cookies) {
    const [key, value] = cookie.trim().split('=');
    if (key === name) return value;
  }
  return null;
}

function checkLanguageStatus() {
  const lang = getCookie("Language");
  if (!lang) {
    locale.value = 'fi';
    return;
  }
  else if (lang === 'fi') {
    locale.value = 'fi';
  }
  else if (lang === 'en') {
    locale.value = 'en';
  }
}

async function checkLogingStatus() {
  try {
    const response = await axios.get('/api/users/me/', {
      withCredentials: true
    });
    dataStore.isLoggedIn = true;
    dataStore.user = response.data;
  } catch (error) {
    dataStore.isLoggedIn = false;
  } finally {
    dataStore.loginChecked = true;
  }
}
// Above are cookie things for auto log  in. Secure since authentication is happening server side
// and token is kept in HttpOnly cookie

onMounted(async() => {
  checkLanguageStatus()
  checkLogingStatus()
  await dataStore.fetchData()
  dataStore.initializePageFromCookies()
  dataStore.isInitialized = true
})
</script>

<template>
  <div v-if="!dataStore.loginChecked || !dataStore.isInitialized" class="loading-screen">
    Loading...
  </div>

  <div v-else>
    <Navigation />
    <Alert />
    <RouterView />
    <TuniFooter />
  </div>
</template>

<style>
.loading-screen {
  height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: bold;
  font-size: 1.2rem;
}
</style>



