<script setup>
import Navigation from './components/Navigation.vue';
import { RouterView } from 'vue-router';
import TuniFooter from './components/Footer.vue';
import Alert from './components/Alert.vue';
import { onMounted } from 'vue';
import { useDataStore } from '@/stores/data';
import axios from 'axios';

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

async function checkLogingStatus() {
  const token = getCookie("Authorization");
  if (!token) {
    dataStore.isLoggedIn = false;
    return;
  }

  try {
    const response = await axios.get('/api/users/me/', {
      headers: {
        Authorization: `Token ${token}`
      }
    });
    dataStore.isLoggedIn = true;
    dataStore.user = response.data;
  } catch (error) {
    dataStore.isLoggedIn = false;

    document.cookie = "Authorization=; Max-age=0";
  }
}
// Above are cookie things for auto log  in. Not very secure since token is kept clientside.

onMounted(() => {
  dataStore.fetchData()
  checkLogingStatus()
})
</script>

<template>
  <Navigation />
  <Alert />
  <RouterView />
  <TuniFooter />
</template>





