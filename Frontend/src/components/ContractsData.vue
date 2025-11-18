<script setup>
import { useAlertStore } from '@/stores/alert';
import { useContractStore } from '@/stores/contract';
import axios from 'axios';
import { computed, ref } from 'vue';
import { useI18n } from 'vue-i18n';
import DetailsOverlay from './DetailsOverlay.vue';

const i18n = useI18n();
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
          <col v-for="(key, index) in $tm('contractHeaders')" :key="key" :style="{ width: columnWidths[index] + 'px' }" />
        </colgroup>
        <thead>
          <tr>
            <th v-for="(key, index) in $tm('contractHeaders')" :key="key" :style="{ width: columnWidths[index] + 'px' }">
              {{ key }}
              <span class="resizer" @mousedown="startResize($event, index)"></span>
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
            <td>
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