<script setup>
import { useDataStore } from '@/stores/data'
import { computed, ref } from 'vue';
import { useI18n } from 'vue-i18n';
import DetailsOverlay from './DetailsOverlay.vue';

const { t } = useI18n();
const store = useDataStore();
const visible = ref(false)
const clickedObject = ref({})

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
  25,
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
  if (sortColumn.value !== columnKey || sortDirection.value === 'none' ) {
    return 'sort-none'
  }
  return sortDirection.value === 'asc' ? 'sort-asc' : 'sort-desc'
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
  console.log(column);
  
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
  visible.value = true
}

const closeOverlay = () => {
  visible.value = false
}

const handleUpdate = (updatedItem) => {
  store.updateObject(updatedItem);
  // Find the updated item in the store's data and update clickedObject
  clickedObject.value = store.data.find(item => item.id === updatedItem.id) || updatedItem;
}

const handleDelete = (itemId) => {
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
      :visible="visible" 
      @close="closeOverlay" 
      @update-item="handleUpdate" 
      @delete-item="handleDelete" 
    />
    <div class="table-container">
      <table>
        <colgroup>
          <col v-for="(key, index) in $tm('tableHeaders')" :key="key" :style="{ width: columnWidths[index] + 'px' }" />
        </colgroup>
        <thead>
          <tr>
            <!-- Käydään läpi sarakeotsikot ja lisätään sort-indikaattori -->
            <!-- Go through the column headers and add a sort indicator -->
            <th v-for="(key, index) in $tm('tableHeaders')" :key="key" :style="{ width: columnWidths[index] + 'px' }">
              <span class="header-text" @click.stop="toggleSort(key)">{{ key }}</span>
              <span class="sort-indicator" :class="getSortClass(key)" @click.stop="toggleSort(key)"></span>
              <span class="resizer" @mousedown="startResize($event, index)"></span>
            </th>
          </tr>
        </thead>

        <tbody>
          <tr  v-for="(item, index) in displayedData" @click="openOverlay(item)" :key="index">
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
.table-container {
  width: 100%;
  overflow-x: auto;
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

.sort-indicator {
  display: inline-block;
  margin-left: 5px;
  position: relative;
  width: 0;
  height: 0;
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
