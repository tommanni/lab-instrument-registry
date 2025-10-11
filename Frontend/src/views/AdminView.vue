<script setup>
import { ref, onMounted } from 'vue';
import TokenOverlay from '@/components/TokenOverlay.vue';
import UserData from '@/components/UserData.vue';
import { useDataStore } from '@/stores/data';
import { useUserStore } from '@/stores/user';
import { useI18n } from 'vue-i18n';
import Search from '@/components/Search.vue';

const { t } = useI18n();

const dataStore = useDataStore();
const userStore = useUserStore();
const loading = ref(true);

onMounted(async () => {
  try {
    await userStore.fetchData();
  } finally {
    loading.value = false;
  }
  // Check for active search terms on page load
  const match = document.cookie.match(/UserSearchTerm=([^;]+)/);
  if (match) {
    userStore.searchData(decodeURIComponent(match[1]));
  } else {
    userStore.searchData(''); // Clear search if no cookie
  }
})
</script>

<template>
  <main v-if="dataStore.isLoggedIn && userStore.user && userStore.user.is_superuser">
    <div class="admins">
      <h2>{{$t('message.adminteksti')}}</h2>
    </div>
    <p></p>
    <ul class="navbar-nav ms-auto mb-2 mb-lg-0">
      <li class="nav-item">
        <TokenOverlay />
      </li>
    </ul>
    <div class="admindata">
      <Search 
        class="user-search-component" 
        :searchFunction="userStore.searchData" 
        cookieName="UserSearchTerm" 
      />
      <UserData />
    </div>
  </main>

  <main v-else-if="!loading">
    <h1 class="text-center"> {{ t('message.admin_ei_oikeuksia') }} </h1>
  </main>
</template>

<style scoped>
main {
  padding-top: 70px;
  padding-left: 20px;
}

.admins h2 {
  white-space: nowrap;
}

.nav-item {
  padding-right: 20px
}

.admindata {
  padding-top: 25px;
  padding-bottom: 88px;
  padding-right: 20px;
  grid-row-start: 2;
  grid-column: 1 / span 3;
}

.user-search-component {
  margin-bottom: 5px;
  margin-left: -10px;
}
</style>
