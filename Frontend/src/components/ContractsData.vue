<script setup>
import { useAlertStore } from '@/stores/alert';
import { useContractStore } from '@/stores/contract';
import axios from 'axios';
import { computed, ref } from 'vue';
import { useI18n } from 'vue-i18n';
import DetailsOverlay from './DetailsOverlay.vue';
import ProductNameInfoPopover from './ProductNameInfoPopover.vue';

const { t, tm, locale } = useI18n();
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
  event.preventDefault();

  const tableEl = event.target.closest('table');
  const minWidth = 40; // px
  // total columns and current widths
  const totalCols = columnWidths.value.length;
  const totalCurrent = columnWidths.value.reduce((s, w) => s + (Number(w) || 0), 0);
  const initialWidth = Number(columnWidths.value[column]) || 120;
  const tableWidth = tableEl ? tableEl.clientWidth : window.innerWidth;

  // compute a conservative max width so other columns won't shrink below minWidth
  const minOtherTotal = Math.max(0, (totalCols - 1) * minWidth);
  const maxWidthCap = Math.max(minWidth + 50, Math.min(800, tableWidth - minOtherTotal));

  let currentWidth = initialWidth;
  let lastClientX = event.clientX;

  // disable text selection while dragging
  const prevUserSelect = document.body.style.userSelect;
  const prevCursor = document.body.style.cursor;
  document.body.style.userSelect = 'none';
  document.body.style.cursor = 'col-resize';

  // pointer capture if available keeps events consistent
  try {
    if (event.pointerId && event.target && event.target.setPointerCapture) {
      event.target.setPointerCapture(event.pointerId);
    }
  } catch (e) { /* ignore */ }

  const onMove = (moveEvent) => {
    // prefer movementX, fallback to delta of clientX
    const clientX = moveEvent.clientX;
    const dx = typeof moveEvent.movementX === 'number' ? moveEvent.movementX : (clientX - lastClientX);
    lastClientX = clientX;

    currentWidth = Math.round(currentWidth + dx);
    if (currentWidth < minWidth) currentWidth = minWidth;
    if (currentWidth > maxWidthCap) currentWidth = maxWidthCap;

    // update reactive widths
    columnWidths.value.splice(column, 1, currentWidth);
  };

  const onUp = () => {
    document.removeEventListener('pointermove', onMove);
    document.removeEventListener('pointerup', onUp);

    try {
      if (event.pointerId && event.target && event.target.releasePointerCapture) {
        event.target.releasePointerCapture(event.pointerId);
      }
    } catch (e) { /* ignore */ }

    // restore styles
    document.body.style.userSelect = prevUserSelect;
    document.body.style.cursor = prevCursor;

    // persist widths
    try { sessionStorage.setItem('dataColumnWidths', JSON.stringify(columnWidths.value)); } catch (e) {}
  };

  document.addEventListener('pointermove', onMove, { passive: false });
  document.addEventListener('pointerup', onUp);
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
              <ProductNameInfoPopover v-if="index === 0" />
            </div>
              <span class="resizer" @pointerdown="startResize($event, index)"></span>
            </th>
          </tr>
        </thead>

        <tbody>
          <tr v-for="(item, index) in Data" @click="openOverlay(item)" data-bs-toggle="modal"
            data-bs-target="#dataModal" :key="index">
            <td>
              {{ locale === 'fi' ? item.tuotenimi : item.tuotenimi_en }}
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

.sort-wrapper {
  display: inline-flex;
  align-items: center;
  gap: 0.2rem;
}

</style>