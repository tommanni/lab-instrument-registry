<script setup>
import { ref, computed, onMounted } from 'vue';
import TokenOverlay from '@/components/TokenOverlay.vue';
import UserData from '@/components/UserData.vue';
import { useDataStore } from '@/stores/data';
import { useUserStore } from '@/stores/user';
import { useI18n } from 'vue-i18n';
import { useRouter, useRoute } from 'vue-router';

const { t } = useI18n();
const router = useRouter();
const route = useRoute();

const dataStore = useDataStore();
const userStore = useUserStore();
const loading = ref(false);

// Determine active tab based on current route
const activeTab = computed(() => {
  const path = route.path;
  if (path.includes('/admin/users')) return 'users';
  if (path.includes('/admin/data-transfer')) return 'data-transfer';
  return 'users'; // default
});

function navigateToTab(tab) {
  const routes = {
    'users': '/admin/users',
    'data-transfer': '/admin/data-transfer'
  };
  router.push(routes[tab]);
}

// Redirect to /admin/users if on /admin root
onMounted(() => {
  if (route.path === '/admin') {
    router.replace('/admin/users');
  }
});
</script>

<template>
  <main v-if="dataStore.isLoggedIn && userStore.user && (userStore.user.is_staff || userStore.user.is_superuser)">
    <div class="admin-header">
      <h2>{{ t('message.adminsivu') }}</h2>
    </div>

    <!-- Tab Navigation -->
    <ul class="nav nav-tabs mb-3">
      <li class="nav-item">
        <a
          class="nav-link"
          :class="{ active: activeTab === 'users' }"
          @click="navigateToTab('users')"
          style="cursor: pointer;"
        >
          {{ t('message.kayttajasivu') }}
        </a>
      </li>
      <li class="nav-item">
        <a
          class="nav-link"
          :class="{ active: activeTab === 'data-transfer' }"
          @click="navigateToTab('data-transfer')"
          style="cursor: pointer;"
        >
          {{ t('message.tiedonsiirto') }}
        </a>
      </li>
    </ul>

    <!-- Router View for Child Routes -->
    <div class="tab-content">
      <router-view />
    </div>
  </main>

  <main v-else-if="!loading">
    <h1 class="text-center"> {{ t('message.admin_ei_oikeuksia') }} </h1>
  </main>
</template>

<style scoped>
main {
  padding-top: 30px;
  padding-left: 20px;
  padding-right: 20px;
  background-color: white;
  min-height: calc(100vh - 70px);
}

.admin-header h2 {
  white-space: nowrap;
  margin-bottom: 20px;
}

.tab-content {
  padding-top: 20px;
}
</style>
