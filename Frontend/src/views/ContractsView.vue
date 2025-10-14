<script setup>
import { onMounted } from 'vue';
import ContractsData from '@/components/ContractsData.vue';
import ContractsPagination from '@/components/ContractsPagination.vue';
import { useContractStore } from '@/stores/contract';
import { useDataStore } from '@/stores/data';

const store = useContractStore();
const dataStore = useDataStore();

onMounted(() => {
  store.fetchData()
})
</script>

<template>
  <main v-if="dataStore.isLoggedIn">
    <div class="contracts">
      <h2>{{$t('message.huoltoteksti')}}</h2>

    </div>
    <div class="contractdata">
      <ContractsData />
      <ContractsPagination />
    </div>
  </main>
  <main v-else>
    <h1 class="text-center"> {{ $t('message.admin_ei_oikeuksia') }} </h1>
  </main>
</template>

<style scoped>

main {
  padding-top: 70px;
  padding-left: 25px;
}

.contracts h2 {
  white-space: nowrap;
}

.contractdata {
  padding-top: 25px;
  padding-bottom: 88px;
  grid-row-start: 2;
  grid-column: 1 / span 3;
  padding-right: 25px;
}

</style>