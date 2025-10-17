<script setup>
import { ref, onMounted } from 'vue';
import Search from '@/components/Search.vue';
import Filter from '@/components/Filter.vue';
import Data from '@/components/Data.vue';
import AddOverlay from '@/components/AddOverlay.vue';
import Pagination from '@/components/Pagination.vue';
import { useDataStore } from '@/stores/data';
const store = useDataStore()
const dataComponent = ref(null)

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
// This only filters once after setting all filters to null
function onAllFiltersCleared(clearedFilters) {
  activateFilters.value = clearedFilters;
  store.filterData({
    yksikko: activateFilters.value.yksikko,
    huone: activateFilters.value.huone,
    vastuuhenkilo: activateFilters.value.vastuuhenkilo,
    tilanne: activateFilters.value.tilanne,
  })
}

function handleNewInstrument(item) {
  if (dataComponent.value) {
    dataComponent.value.openOverlay(item);
  }
}
</script>

<template>
    <div class="home-root">
      <div class="actions-wrapper py-2 px-3 gap-2 mb-2 rounded" style="z-index: 10;">
        <div class="d-flex"><Search :searchFunction="store.searchData" cookieName="InstrumentSearchTerm" /></div>
        <div class="f-wrapper">
          <Filter @filter-change="onFilterChange" @all-filters-cleared="onAllFiltersCleared" />
        </div>
        <div class="d-flex align-items-center justify-content-end ms-auto">
          <AddOverlay @new-instrument-added="handleNewInstrument" />
        </div>
      </div>
      <div class="data">
        <Data ref="dataComponent" />
        <Pagination />
      </div>
    </div>
</template>

<style scoped>

.home-root {
  display: flex;
  flex-direction: column;
  box-sizing: border-box;
  height: 100%;
}


.actions-wrapper {
  display: flex;
  position: sticky;
  width: 100%;
  top: var(--header-height);
  grid-template-columns: 2fr 4fr 1fr;
  background: var(--bs-secondary-bg-subtle);
  z-index: 11;
  box-sizing: border-box;
  flex-wrap: wrap;
}

.f-wrapper {
  display: grid;
  grid-template-columns: 70% 30%;
  flex: 1;
}

@media screen and (max-width: 768px){
  .actions-wrapper {
    position: static;
  }
  .f-wrapper {
    width: 100%;
  }
}

</style>
