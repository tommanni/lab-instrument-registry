<script setup>
import { RouterLink } from 'vue-router'
import LangButton from './LangButton.vue';
import { useDataStore } from '@/stores/data';
import LogoutOverlay from './LogoutOverlay.vue';
import LoginOverlay from './LoginOverlay.vue';
import RegisterOverlay from './RegisterOverlay.vue';
import { useMediaQuery } from '@vueuse/core';

const dataStore = useDataStore()
const isMobile = useMediaQuery('(max-width: 768px');

</script>

<template>
  <header
    class="d-flex justify-content-space-between py-3 mb-4 border-bottom px-3 align-items-center fixed-top bg-body-tertiary">
    <a v-if="!isMobile" class="d-flex align-items-center px-4 fw-bold fs-5 text-decoration-none" href="/">
      Metlabs Registry
    </a>
    <ul class="nav flex-1  align-items-center mb-md-0 gap-1">
      <li class="nav-item">
        <RouterLink v-if="isMobile" class="bi bi-house-door btn btn-primary fs-5" to="/"/>
        <RouterLink v-else class="nav-link" to="/">{{$t('message.kotisivu') }}</RouterLink>
      </li>
      <li v-if="dataStore.isLoggedIn" class="nav-item">
        <RouterLink v-if="isMobile" class="bi bi-card-checklist btn btn-primary fs-5" to="/contracts"/>
        <RouterLink v-else class="nav-link" to="/contracts">{{ $t('message.huoltosivu') }}</RouterLink>
      </li>
      <li v-if="dataStore.isLoggedIn" class="nav-item">
        <RouterLink v-if="isMobile" class="bi bi-people btn btn-primary fs-5" to="/admin"/>
        <RouterLink v-else class="nav-link" to="/admin">{{ $t('message.kayttajasivu') }}</RouterLink>
      </li>
      
    </ul>
    <div class="d-flex align-items-center">
      <LangButton class="me-2"/>
      <LogoutOverlay />
      <LoginOverlay />
      <RegisterOverlay />
    </div>
  </header>
</template>

<style scoped>

header {
  height: var(--header-height);
  box-sizing: border-box;
}

.router-link-active {
  border-bottom: 1px solid var(--bs-primary);
  font-weight: 600;
}

header ul {
  flex: 1;
}

</style>