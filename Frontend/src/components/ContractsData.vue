<script setup>
import { useAlertStore } from '@/stores/alert';
import { useContractStore } from '@/stores/contract';
import axios from 'axios';
import { computed, ref } from 'vue';
import { useI18n } from 'vue-i18n';
import DetailsOverlay from './DetailsOverlay.vue';

const { t, tm } = useI18n();
const store = useContractStore();
const clickedObject = ref({})
const alertStore = useAlertStore()

const columnWidths = ref([
  50,
  50,
  50,
  50,
  50
]);

const headerMap = {
  [tm('contractHeaders')[0]] : 'tuotenimi',
  [tm('contractHeaders')[1]] : 'seuraava_huolto',
  [tm('contractHeaders')[2]] : 'edellinen_huolto',
  [tm('contractHeaders')[3]] : 'vastuuhenkilo',
  [tm('contractHeaders')[4]] : 'huoltosopimus_loppuu'
};

// Sort table by column (asc -> desc -> none)
function sortBy(key) {
  if (store.sortColumn === key) {
    store.sortDirection =
      store.sortDirection === 'asc'
        ? 'desc'
        : store.sortDirection === 'desc'
        ? 'none'
        : 'asc';
  } else {
    store.sortColumn = key;
    store.sortDirection = 'asc';
  }
  // Sort data
  store.updateVisibleData();
}

// Get CSS class for sort icon
function getSortClass(columnKey) {
  if (store.sortColumn !== columnKey || store.sortDirection === 'none') {
    return 'bi bi-caret-down text-body-tertiary'
  }
  return store.sortDirection === 'asc' ? 'bi bi-caret-up-fill text-primary' : 'bi bi-caret-down-fill text-primary'
}

const Data = computed(() => store.data);

// Handle column resizing
const startResize = (event, column) => {
  const startX = event.clientX;
  const startWidth = columnWidths.value[column];

  const onMouseMove = (moveEvent) => {
    const newWidth = startWidth + (moveEvent.clientX - startX);
    columnWidths.value[column] = Math.max(newWidth, 25);
  };

  const onMouseUp = () => {
    document.removeEventListener("mousemove", onMouseMove);
    document.removeEventListener("mouseup", onMouseUp);
  };

  document.addEventListener("mousemove", onMouseMove);
  document.addEventListener("mouseup", onMouseUp);
};

const openOverlay = (item) => {
  clickedObject.value = {...item}
}

const handleUpdateItem = (updatedItem) => {
  store.updateObject(updatedItem)
  clickedObject.value = updatedItem
}
</script>

<template>
  <div>
    <DetailsOverlay
      :item="clickedObject"
      :allow-delete="false"
      @update-item="handleUpdateItem"
    />
    
    <div class="table-container">
      <table>
        <colgroup>
          <col v-for="(key, index) in tm('contractHeaders')" :key="key" :style="{ width: columnWidths[index] + 'px' }" />
        </colgroup>
        <thead>
          <tr>
            <th
            v-for="(key, index) in tm('contractHeaders')"
            :key="key"
            :style="{ width: columnWidths[index] + 'px' }">
            <div class="sort-wrapper" @click.stop="sortBy(headerMap[key])" style="cursor: pointer;">
              <span v-if="index === 1">
              <i v-if="store.isUrgent > 0" class="bi bi-exclamation-circle-fill text-danger" style="margin-right: 5px;"></i>
              <i v-else-if="store.isUpcoming > 0" class="bi bi-exclamation-circle-fill text-warning" style="margin-right: 5px;"></i>
              </span>
              <span v-if="index === 4">
              <i v-if="store.isEnded > 0" class="bi bi-exclamation-circle-fill text-danger" style="margin-right: 5px;"></i>
              <i v-else-if="store.isEnding > 0" class="bi bi-exclamation-circle-fill text-warning" style="margin-right: 5px;"></i>
              </span>
              <span class="header-text">{{ key }}</span>
              <i :class="getSortClass(headerMap[key])"></i>
            </div>
              <span class="resizer" @pointerdown="startResize($event, index)"></span>
            </th>
          </tr>
        </thead>

        <tbody>
          <tr v-for="(item, index) in Data" @click="openOverlay(item)" data-bs-toggle="modal"
            data-bs-target="#dataModal" :key="index">
            <td>
              {{ item.tuotenimi }}
            </td>
            <td v-if="store.isMaintenanceUpcoming(item.seuraava_huolto)" class="upcoming">
              {{ item.seuraava_huolto }}
            </td>
            <td v-else-if="store.isMaintenanceDue(item.seuraava_huolto)" class="urgent">
              {{ item.seuraava_huolto }}
            </td>
            <td v-else>
              {{ item.seuraava_huolto }}
            </td>
            <td>
              {{ item.edellinen_huolto }}
            </td>
            <td>
              {{ item.vastuuhenkilo }}
            </td>
            <td v-if="store.isMaintenanceUpcoming(item.huoltosopimus_loppuu)" class="upcoming">
              {{ item.huoltosopimus_loppuu }}
            </td>
            <td v-else-if="store.isMaintenanceDue(item.huoltosopimus_loppuu)" class="urgent">
              {{ item.huoltosopimus_loppuu }}
            </td>
            <td v-else>
              {{ item.huoltosopimus_loppuu }}
            </td>
          </tr>
        </tbody>
      </table>
    </div>
  </div>
</template>

<style scoped>
.table-container {
  display: block !important;
  width: 100% !important;
  margin-left: 0 !important;
  justify-self: start !important;
  grid-column: 1 !important;
}

table {
  width: 100%;
  border-collapse: collapse;
  table-layout: fixed;
}

th, td {
  border: 1px solid #ddd;
  padding: 8px;
  position: relative;
  text-align: left;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

th {
  background: #f4f4f4;
  position: relative;
}

tbody tr {
  cursor: pointer;
  transition: background-color 0.2s ease;
}

tbody tr:hover {
  background-color: #f0f0f0;
}

.resizer {
  position: absolute;
  right: 0;
  top: 0;
  width: 5px;
  height: 100%;
  cursor: col-resize;
  background: transparent;
}

.resizer:hover {
  background: #ab9bcb;
}

.urgent {
  background-color: red;
  color: white;
}

.upcoming {
  background-color: yellow;
}

</style>