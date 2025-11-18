<script setup>
import { ref, onMounted } from 'vue';
import ContractsData from '@/components/ContractsData.vue';
import Pagination from '@/components/Pagination.vue';
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
})
</script>

<template>
  <div class="screen-container">
    <div v-if="loading" class="loading-screen">
      Loading...
  </div>
  <main v-else>
    <div class="contracts">
      <h2>{{ t('message.huoltoteksti') }}</h2>
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