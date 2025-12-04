<script setup>
import Navigation from './components/Navigation.vue';
import { RouterView } from 'vue-router';
import TuniFooter from './components/Footer.vue';
import Alert from './components/Alert.vue';
import { onMounted, onBeforeUnmount } from 'vue';
import { useDataStore } from '@/stores/data';
import { useUserStore } from './stores/user';
import { useContractStore } from '@/stores/contract';
import axios from 'axios';
import { useI18n } from 'vue-i18n';

const { t, locale } = useI18n()

const dataStore = useDataStore();
const userStore = useUserStore();
const contractStore = useContractStore();

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
    await contractStore.fetchData()
  } catch (error) {
    dataStore.isLoggedIn = false;
  } finally {
    dataStore.loginChecked = true;
  }
}

async function checkShibbolethAuth() {
  // Request a simple resource that requires Shibboleth
  // This will redirect to Shibboleth IDP if not authenticated
  // but we use a non-XHR approach so redirects work
  try {
    // Try to access a public endpoint that SHOULD work if Shibboleth is satisfied
    const response = await fetch('/api/instruments/valueset/yksikko/', {
      credentials: 'include'
    });
    // If API returns data, we're authenticated
    const hasData = response.ok && response.status === 200;
    return hasData;
  } catch (error) {
    console.warn('Auth check failed:', error);
    return false;
  }
}

// Above are cookie things for auto log  in. Secure since authentication is happening server side
// and token is kept in HttpOnly cookie

onMounted(async () => {
  checkLanguageStatus()

  const shibAuth = await checkShibbolethAuth();
  if (!shibAuth) {
    console.warn('Waiting for Shibboleth authentication...');
    // Redirect user to Shibboleth login
    window.location.href = '/Shibboleth.sso/Login?target=' + encodeURIComponent(window.location.href);
    return;
  }

  checkLogingStatus()
  await dataStore.fetchData()
  await dataStore.initializePageFromURL()
  dataStore.isInitialized = true;

  // --- start session monitor & intercept 401s ---
  // BroadcastChannel so other tabs/windows get logout notifications
  const bc = (typeof BroadcastChannel !== 'undefined') ? new BroadcastChannel('auth') : null;
  if (bc) {
    bc.onmessage = (ev) => {
      if (ev.data?.type === 'logout') {
        dataStore.isLoggedIn = false;
        dataStore.user = null;
        userStore.user = null;
        userStore.fullData = null;
        userStore.searchedData = null;
        userStore.currentData = null;
        contractStore.originalData = null;
        contractStore.contractData = null;
        contractStore.data = null;
        dataStore.loginChecked = true;
      }
    }
  }

  // Axios interceptor: mark logged out on 401 responses
  const interceptor = axios.interceptors.response.use(
    res => res,
    err => {
      if (err?.response?.status === 401) {
        dataStore.isLoggedIn = false;
        dataStore.user = null;
        userStore.user = null;
        userStore.fullData = null;
        userStore.searchedData = null;
        userStore.currentData = null;
        contractStore.originalData = null;
        contractStore.contractData = null;
        contractStore.data = null;
        dataStore.loginChecked = true;
        if (bc) bc.postMessage({ type: 'logout' });
      }
      return Promise.reject(err);
    }
  );

  // Periodic session check
  const intervalMs = 30_000; // 30s, adjust as needed
  const monitorId = setInterval(async () => {
    try {
      const resp = await axios.get('/api/users/me/', { withCredentials: true });
      // if previously logged out, restore user info
      if (!dataStore.isLoggedIn) {
        dataStore.isLoggedIn = true;
        dataStore.user = resp.data;
      }
      dataStore.loginChecked = true;
    } catch (e) {
      if (e?.response?.status === 401) {
        dataStore.isLoggedIn = false;
        dataStore.user = null;
        userStore.user = null;
        userStore.fullData = null;
        userStore.searchedData = null;
        userStore.currentData = null;
        contractStore.originalData = null;
        contractStore.contractData = null;
        contractStore.data = null;
        dataStore.loginChecked = true;
        if (bc) bc.postMessage({ type: 'logout' });
      }
    }
  }, intervalMs);

  // make cleanup info available to onBeforeUnmount via element closure
  // store them on window to be accessible in unmount block below
  window.__sessionMonitor = { monitorId, interceptor, bc };
})

// add cleanup so interceptor and interval are removed when App unmounts
onBeforeUnmount(() => {
  const s = window.__sessionMonitor;
  if (s) {
    if (s.monitorId) clearInterval(s.monitorId);
    if (s.interceptor !== undefined) axios.interceptors.response.eject(s.interceptor);
    if (s.bc) s.bc.close();
    delete window.__sessionMonitor;
  }
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
