<script setup>
import { RouterLink } from 'vue-router';
import LangButton from './LangButton.vue';
import { useDataStore } from '@/stores/data';
import { useUserStore } from '@/stores/user';
import { ref, onMounted, watch } from 'vue';
import axios from 'axios';
import { useI18n } from 'vue-i18n';
import { useAlertStore } from '@/stores/alert';
import LogoutOverlay from './LogoutOverlay.vue';
import LoginOverlay from './LoginOverlay.vue';
import RegisterOverlay from './RegisterOverlay.vue';
import { useMediaQuery } from '@vueuse/core';

const { t } = useI18n();

const dataStore = useDataStore();
const userStore = useUserStore();
const alertStore = useAlertStore();
const isMobile = useMediaQuery('(max-width: 768px');

onMounted(() => {
  // Get current user (null if not logged in)
  userStore.fetchUser();
})

watch(() => dataStore.isLoggedIn, (isLoggedIn) => {
  // Refetch user when login status changes
  userStore.fetchUser();
});

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
        <RouterLink v-else class="nav-link" to="/">{{ t('message.kotisivu') }}</RouterLink>
      </li>
      <li v-if="dataStore.isLoggedIn && userStore.user" class="nav-item">
        <RouterLink v-if="isMobile" class="bi bi-person btn btn-primary fs-5" :to="`/users/${userStore.user.id}`"/>
        <RouterLink v-else class="nav-link" :to="`/users/${userStore.user.id}`">{{ t('message.omat_tiedot') }}</RouterLink>
      </li>
      <li v-if="dataStore.isLoggedIn" class="nav-item">
        <RouterLink v-if="isMobile" class="bi bi-wrench btn btn-primary fs-5" to="/contracts"/>
        <RouterLink v-else class="nav-link" to="/contracts">{{ t('message.huoltosivu') }}</RouterLink>
      </li>
      <li v-if="dataStore.isLoggedIn && userStore.user && userStore.user.is_superuser" class="nav-item">
        <RouterLink v-if="isMobile" class="bi bi-people btn btn-primary fs-5" to="/admin"/>
        <RouterLink v-else class="nav-link" to="/admin">{{ t('message.adminsivu') }}</RouterLink>
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

header ul {
  flex: 1;
}
</style>