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


function onFilterChange({ filterName, value }) {
  store.filterValues[filterName] = value
  store.filterData()
}
// This only filters once after setting all filters to null
function onAllFiltersCleared(clearedFilters) {
  store.filterValues = clearedFilters;
  store.filterData();
}

function handleNewInstrument(item) {
  if (dataComponent.value) {
    dataComponent.value.openOverlay(item);
  }
}
</script>

<template>
    <div class="home-root">
      <div class="actions-wrapper p-2 gap-2 mb-2" style="z-index: 10;">
        <div class="actions-add">
          <AddOverlay @new-instrument-added="handleNewInstrument" />
        </div>
        <div class="actions-line actions-line--search">
          <Search :searchFunction="store.searchData" searchType="device" />
        </div>
        <div class="actions-line actions-line--filters">
          <Filter @filter-change="onFilterChange" @all-filters-cleared="onAllFiltersCleared" />
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
  display: grid;
  grid-template-columns: 1fr;
  grid-template-areas:
    "search"
    "filters"
    "add";
  position: sticky;
  width: 100%;
  top: var(--header-height);
  background: var(--bs-secondary-bg-subtle);
  z-index: 11;
  box-sizing: border-box;
  justify-items: stretch;
}

.actions-line {
  width: 100%;
  display: flex;
  justify-content: center;
  align-items: flex-start;
}

.actions-line--search {
  grid-area: search;
  box-sizing: border-box;
}

.actions-line--filters {
  grid-area: filters;
  flex-wrap: wrap;
  gap: 0.5rem;
}

.actions-add {
  grid-area: add;
  justify-self: center;
}

@media screen and (min-width: 992px){
  .actions-wrapper {
    grid-template-columns: 1fr auto;
    grid-template-areas:
      "search add"
      "filters add";
    align-items: start;
  }
  .actions-add {
    justify-self: flex-end;
    align-self: start;
  }
}

@media screen and (max-width: 768px){
  .actions-wrapper {
    position: static;
    justify-items: stretch;
  }
  .actions-line--filters {
    flex-direction: column;
    align-items: center;
  }
  .actions-add {
    margin-top: 0;
    width: 100%;
    display: block;
    justify-self: stretch;
  }
}

</style>
