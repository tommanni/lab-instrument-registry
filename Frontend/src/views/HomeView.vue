<script setup>
import { ref, onMounted } from 'vue';
import Search from '@/components/Search.vue';
import Filter from '@/components/Filter.vue';
import Data from '@/components/Data.vue';
import AddOverlay from '@/components/AddOverlay.vue';
import LoginOverlay from '@/components/LoginOverlay.vue';
import Pagination from '@/components/Pagination.vue';
import { useDataStore } from '@/stores/data';
import RegisterOverlay from '@/components/RegisterOverlay.vue';
const store = useDataStore()

const activateFilters = ref({
  yksikko : null,
  huone: null,
  vastuuhenkilo: null,
  tilanne: null
})
function onFilterChange({ filterName, value }) {
  activateFilters.value[filterName] = value
  store.filterData({
    yksikko: activateFilters.value.yksikko,
    huone: activateFilters.value.huone,
    vastuuhenkilo: activateFilters.value.vastuuhenkilo,
    tilanne: activateFilters.value.tilanne,
  })
}
</script>

<template>
  <main>
    <Filter @filter-change="onFilterChange" />
    <Search />
    <ul class="navbar-nav ms-auto mb-2 mb-lg-0">
      <li class="nav-item">
        <AddOverlay />
      </li>
    </ul>
    <LoginOverlay />
    <RegisterOverlay />
    <div class="data">
      <Data />
      <Pagination />
    </div>
  </main>
</template>

<style scoped>
main {
  padding-top: 65px;
}
.data {
  padding-bottom: 88px;
  padding-top: 5px
}

.nav-item {
  margin-right: 20px;
}

</style>