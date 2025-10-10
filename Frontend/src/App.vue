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

onMounted(async () => {
  checkLanguageStatus()
  checkLogingStatus()
  await dataStore.fetchData()
  dataStore.initializePageFromCookies()
  dataStore.isInitialized = true;
})




</script>

<template>
  <div class="screen-container">
    <div v-if="!dataStore.loginChecked || !dataStore.isInitialized" class="loading-screen">
      Loading...
    </div>

    <div v-else class="layout">
      <div class="main-wrapper">
        <div id="nw-1" class="navigation-wrapper">
           <Navigation />
        </div>
        <Alert />
        <div id="c1" class="content">
          <div class="main-content-wrapper p-2">
            <RouterView />
          </div>
        </div>
        <div class="content-bottom">
          <TuniFooter />
        </div>
      </div>

    </div>
  </div>

</template>

<style>

.screen-container {
  display: flex;
  flex-direction: column;
  height: 100vh;
  overflow-x: hidden;
  overflow-y: auto;
  background-color: var(--bs-light-bg-subtle);
}

.layout {
  -webkit-box-orient: vertical;
  -webkit-box-direction: normal;
  -ms-flex-direction: column;
  flex-direction: column;
  display: -webkit-box;
  display: -ms-flexbox;
  display: flex;
  min-height: 100vh;
}

.navigation-wrapper {
  position: sticky;
  top: 0;
  z-index: 1030;
  height: var(--header-height)
}

.layout .main-wrapper {
  display: -webkit-box;
  display: -ms-flexbox;
  display: flex;
  -webkit-box-flex: 1;
  -ms-flex: 1;
  flex: 1;
  -webkit-box-orient: vertical;
  -webkit-box-direction: normal;
  -ms-flex-direction: column;
  flex-direction: column;
  box-sizing: border-box;
}

.layout .content {
  display: -webkit-box;
  display: -ms-flexbox;
  display: flex;
  -webkit-box-flex: 1;
  -ms-flex: 1;
  flex: 1;
  -webkit-box-orient: vertical;
  -webkit-box-direction: normal;
  -ms-flex-direction: column;
  flex-direction: column;
  position: relative;
  box-sizing: border-box;
}

.layout .content-bottom {
  bottom: 0;
  /*position: sticky;*/
  z-index: 100;
}

.content .main-content-wrapper {
  -webkit-box-flex: 1;
  -ms-flex: 1;
  flex: 1;
  position: relative;
  box-sizing: border-box;
  margin: 0 auto;
  width: 100%;
}

.loading-screen {
  height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: bold;
  font-size: 1.2rem;
}
</style>
