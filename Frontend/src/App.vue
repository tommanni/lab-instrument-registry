<script setup>
import Navigation from './components/Navigation.vue';
import { RouterView } from 'vue-router';
import TuniFooter from './components/Footer.vue';
import Alert from './components/Alert.vue';
import { onMounted } from 'vue';
import { useDataStore } from '@/stores/data';

const dataStore = useDataStore()

onMounted(() => {
  dataStore.fetchData()
})
</script>

<template>
  <Navigation />
  <Alert />
  <RouterView />
  <TuniFooter />
</template>





