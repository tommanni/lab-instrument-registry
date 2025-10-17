<script setup>
import { useDataStore } from '@/stores/data'
import { computed, ref } from 'vue';
import { useI18n } from 'vue-i18n';
import DetailsOverlay from './DetailsOverlay.vue';
import { useMediaQuery } from '@vueuse/core';

const { t } = useI18n();
const store = useDataStore();
const clickedObject = ref({})
const isMobile = useMediaQuery('(max-width: 768px');

// Sarakkeet:
// Columns:
const headerToKey = {
  "Tuotenimi": "tuotenimi",
  "Merkki ja malli": "merkki_ja_malli",
  "Yksikkö": "yksikko",
  "Kampus": "kampus",
  "Rakennus": "rakennus",
  "Huone": "huone",
  "Vastuuhenkilö": "vastuuhenkilo",
  "Tilanne": "tilanne",
  "Product Name": "tuotenimi",
  "Brand and Model": "merkki_ja_malli",
  "Unit": "yksikko",
  "Campus": "kampus",
  "Building": "rakennus",
  "Room": "huone",
  "Person in charge": "vastuuhenkilo",
  "Status": "tilanne"
}

// Lajittelu: mikä sarake ja mikä suunta (asc, desc, none)
// Sorting: which column and which direction (asc, desc, none)
const sortColumn = ref('')
const sortDirection = ref('none')
// DEMO
const columnWidths = ref([
  50,
  50,
  50,
  30,
  30,
  45,
  50,
  30
  ]);

// Lajittelun hallinta klikkaamalla
// Toggling sorting by clicking
function toggleSort(columnKey) {
  if (sortColumn.value !== columnKey) {
    // Uusi sarake: aloitetaan lajittelu nousevaksi
    // New column: start with ascending sorting
    sortColumn.value = columnKey
    sortDirection.value = 'asc'
  }
  else {
    // Sama sarake: järjestyksen suunta vaihtuu
    // Same column: switch the direction of sorting
    if (sortDirection.value === 'asc') {
      sortDirection.value = 'desc'
    }
    else if (sortDirection.value === 'desc') {
      // Kolmannella klikkauksella palautuu 'none'
      // On the third click return to 'none'
      sortColumn.value = ''
      sortDirection.value = 'none'
    }
  }
}

// CSS-luokan palautus lajittelun tilan perusteella
// Returning of the CSS class by the state of the sorting
function getSortClass(columnKey) {
  if (sortColumn.value !== columnKey || sortDirection.value === 'none') {
    return 'bi bi-caret-down text-body-tertiary'
  }
  return sortDirection.value === 'asc' ? 'bi bi-caret-up-fill text-primary' : 'bi bi-caret-down-fill text-primary'
}

// Lajitellaan näytettävä data
// Aktiivinen lajittelutila lajittelee datan ennen sivutusta
// Sort visible data
// Active sorting mode sorts data before paging
const displayedData = computed(() => {
  // Perusaineiston haku
  // Retrieve base data
  let baseData = store.searchedData || []
  if (!sortColumn.value || sortDirection.value === 'none') {
    // Ilman lajittelua sivutetaan normaalisti
    // Without sorting page normally
    return store.data
  }
  else {
    // Tehdään kopio kokonaisdatasta
    // Make a copy of all data
    let sorted = [...baseData]
    const key = headerToKey[sortColumn.value] || sortColumn.value
    sorted.sort((a, b) => {
      const valA = (a[key] || '').toString().toLowerCase()
      const valB = (b[key] || '').toString().toLowerCase()
      const comp = valA.localeCompare(valB)
      return sortDirection.value === 'asc' ? comp : -comp
    })
    // Käytetään normaalia sivutusta
    // Use normal paging
    const start = (store.currentPage - 1) * 15
    const end = store.currentPage * 15
    return sorted.slice(start, end)
  }
})

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
  clickedObject.value = { ...item }
}

const handleUpdateItem = (updatedItem) => {
  store.updateObject(updatedItem);
  clickedObject.value = updatedItem
}

const handleDeleteItem = (itemId) => {
  store.deleteObject(itemId);
}

defineExpose({
  openOverlay
});
</script>

<template>
  <div>
    <DetailsOverlay
      :item="clickedObject"
      @update-item="handleUpdateItem"
      @delete-item="handleDeleteItem"
    />
    <div class="tuni-table-wrapper table-responsive-sm shadow-sm"> <!--class="table-container rounded shadow-sm"-->
      <table class='table table-hover border-radius-sm '>
        <colgroup>
          <col v-for="(key, index) in $tm('tableHeaders')" :key="key" :style="{ width: columnWidths[index] + 'px' }" />
        </colgroup>
        <thead class="table-secondary">
          <tr>
            <!-- Käydään läpi sarakeotsikot ja lisätään sort-indikaattori -->
            <!-- Go through the column headers and add a sort indicator -->
            <th class="tuni-table-header-cell" v-for="(key, index) in $tm('tableHeaders')" :key="key" :style="{ width: columnWidths[index] + 'px' }">
              <div class="sort-wrapper">
              <span class="header-text" @click.stop="toggleSort(key)">{{ key }}</span>

                <i :class="getSortClass(key)" @click.stop="toggleSort(key)"></i>
              </div>
              <span class="resizer" @mousedown="startResize($event, index)"></span>
            </th>
          </tr>
        </thead>

        <tbody>
          <tr v-for="(item, index) in displayedData" @click="openOverlay(item)" data-bs-toggle="modal"
            data-bs-target="#dataModal" :key="index">
            <td>
              {{ item.tuotenimi }}
            </td>
            <td>
              {{ item.merkki_ja_malli }}
            </td>
            <td>
              {{ item.yksikko }}
            </td>
            <td>
              {{ item.kampus }}
            </td>
            <td>
              {{ item.rakennus }}
            </td>
            <td>
              {{ item.huone }}
            </td>
            <td>
              {{ item.vastuuhenkilo }}
            </td>
            <td>
              {{ item.tilanne }}
            </td>
          </tr>
        </tbody>
      </table>
    </div>
  </div>
</template>

<style scoped>


.sort-wrapper {
  width: 100%;
  display: flex;
  gap: 0.5rem;
  align-items: end;
}

table {
  width: 100%;
  border-collapse: separate;
  border-spacing: 0;
  table-layout: fixed;
  border-radius: 8px;
}

th,
td {
  /*border: 1px solid #ddd;*/
  padding: 8px;
  position: relative;
  text-align: left;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  border-bottom: var(--bs-border-width) var(--bs-border-style) var(--bs-border-color);
}

th {
  background-color: var(--bs-secondary-bg-subtle);
  position: sticky;
  top: calc(var(--header-height) + 56px);
  z-index: 1;
}

/* Round top corners of header */
thead tr:first-child th:first-child {
  border-top-left-radius: 8px;
}

thead tr:first-child th:last-child {
  border-top-right-radius: 8px;
}

/* Round bottom corners of last row */
tbody tr:last-child td:first-child {
  border-bottom-left-radius: 8px;
}

tbody tr:last-child td:last-child {
  border-bottom-right-radius: 8px;
}

tbody tr {
  cursor: pointer;
  transition: background-color 0.2s ease;
}

tbody tr:hover {
  background-color: #f0f0f0;
}

/* Round bottom corners of the last row */
tbody tr:last-child td:first-child {
  border-bottom-left-radius: 8px;
}

tbody tr:last-child td:last-child {
  border-bottom-right-radius: 8px;
}

.sort-wrapper i {
  font-size: small;
}

.sort-indicator {
  margin-left: 5px;
  position: static;
  width: 0;
  height: 0;
  margin-left: 10px;
}

.sort-indicator.sort-none::before,
.sort-indicator.sort-none::after {
  content: '';
  display: inline-block;
  border-left: 4px solid transparent;
  border-right: 4px solid transparent;
}

.sort-indicator.sort-none::before {
  border-bottom: 4px solid #ccc;
  margin-right: 2px;
}

.sort-indicator.sort-none::after {
  border-top: 4px solid #ccc;
}

.sort-indicator.sort-asc::before {
  content: '';
  display: inline-block;
  border-left: 4px solid transparent;
  border-right: 4px solid transparent;
  border-bottom: 4px solid #4E008E;
}

.sort-indicator.sort-asc::after {
  content: none;
}

.sort-indicator.sort-desc::after {
  content: '';
  display: inline-block;
  border-left: 4px solid transparent;
  border-right: 4px solid transparent;
  border-top: 4px solid #4E008E;
}

.sort-indicator.sort-desc::before {
  content: none;
}

.header-text {
  cursor: pointer;
}
</style>