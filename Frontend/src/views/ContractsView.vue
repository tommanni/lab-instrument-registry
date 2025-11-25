<script setup>
import { ref, onMounted, watch } from 'vue';
import ContractsData from '@/components/ContractsData.vue';
import Pagination from '@/components/Pagination.vue';
import Search from '@/components/Search.vue';
import { useContractStore } from '@/stores/contract';
import { useDataStore } from '@/stores/data';
import { useUserStore } from '@/stores/user';
import { useI18n } from 'vue-i18n';
import { useRouter, useRoute } from 'vue-router';

const { t } = useI18n();

const store = useContractStore();
const dataStore = useDataStore();
const userStore = useUserStore();
const loading = ref(true);
const router = useRouter();
const route = useRoute();

onMounted(async () => {
  try {
    await store.fetchData();
  } finally {
    loading.value = false;
  }
  const p = route.query.page ? parseInt(route.query.page, 10) : 1
  store.currentPage = Number.isNaN(p) ? 1 : p

  // Redirect
  if (!dataStore.isLoggedIn) {
    router.replace('/');
  }
})
// watcher for login status
watch(() => dataStore.isLoggedIn, (isLoggedIn) => {
  if (!loading.value && !isLoggedIn) {
    router.replace('/');
  }
})
</script>

<template>
  <div v-if="dataStore.isLoggedIn" class="screen-container">
    <div v-if="loading" class="loading-screen">
      Loading...
    </div>
    <main v-else>
      <div class="contracts">
        <h2>{{ t('message.huoltoteksti') }}</h2>
      </div>
      <div class="actions-line actions-line--search">
          <Search :searchFunction="store.searchData" searchType="contract" />
      </div>
      <div class="contractdata">
        <ContractsData />
        <Pagination :store="store" v-if="store.numberOfPages > 1"/>
      </div>
    </main>
  </div>
</template>

<style scoped>
main {
  padding-top: 30px;
  padding-left: 20px;
  padding-right: 20px;
}

.contracts h2 {
  white-space: nowrap;
}

.contractdata {
  padding-top: 20px;
  padding-bottom: 88px;
  grid-row-start: 2;
  grid-column: 1 / span 3;
}
</style>