<script setup>
import { RouterLink } from 'vue-router'
import LangButton from './LangButton.vue';
import { useDataStore } from '@/stores/data';

const dataStore = useDataStore()
</script>

<template>
  <header>
      <nav class="navbar navbar-expand-lg bg-body-tertiary fixed-top">
        <div class="container-fluid">
          <ul class="navbar-nav me-auto mb-2 mb-lg-0">
            <li class="nav-item">
              <RouterLink class="nav-link" to="/">{{$t('message.kotisivu')}}</RouterLink>
            </li>
            <li v-if="dataStore.isLoggedIn" class="nav-item">
              <RouterLink class="nav-link" to="/contracts">{{$t('message.huoltosivu')}}</RouterLink>
            </li>
            <li v-if="dataStore.isLoggedIn" class="nav-item">
              <RouterLink class="nav-link" to="/admin">{{$t('message.kayttajasivu')}}</RouterLink>
            </li>
          </ul>

          <ul class="navbar-nav ms-auto mb-2 mb-lg-0">
            <li class="nav-item">
             <LangButton />
            </li>
          </ul>
          
        </div>
        
      </nav>
  </header>
</template>

<style scoped>
header {
  width: 100%;
  position: fixed;
  top: 0;
}
</style>