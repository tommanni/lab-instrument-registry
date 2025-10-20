<script setup>
import { ref, onMounted } from 'vue';
import TokenOverlay from '@/components/TokenOverlay.vue';
import UserData from '@/components/UserData.vue';
import { useDataStore } from '@/stores/data';
import { useUserStore } from '@/stores/user';
import { useI18n } from 'vue-i18n';
import Search from '@/components/Search.vue';
import { useRouter, useRoute } from 'vue-router';

const userStore = useUserStore();
const loading = ref(true);
const router = useRouter();
const route = useRoute();

onMounted(async () => {
  try {
    await userStore.fetchData();
  } finally {
    loading.value = false;
  }
  // Check for active search terms on page load
  userStore.searchTerm = route.query.search ?? ''
  if (userStore.searchTerm) {
    userStore.searchData();
  } else {
    userStore.searchData(true); // Clear search if no terms
  }
})
</script>

<template>
  <div>
    <ul class="navbar-nav ms-auto mb-2 mb-lg-0">
      <li class="nav-item">
        <TokenOverlay />
      </li>
    </ul>
    <div class="admindata">
      <Search
        :searchFunction="userStore.searchData"
        searchType="user"
      />
      <UserData />
    </div>
  </div>
</template>

<style scoped>
.nav-item {
  padding-right: 20px
}

.admindata {
  padding-top: 25px;
  padding-bottom: 88px;
  grid-row-start: 2;
  grid-column: 1 / span 3;
}

.user-search-component {
  margin-bottom: 5px;
  margin-left: -10px;
}
</style>
