<script setup>
import { useDataStore } from '@/stores/data'
import { computed, ref, onMounted, nextTick } from 'vue';
import { useI18n } from 'vue-i18n';
import DetailsOverlay from './DetailsOverlay.vue';
import { useMediaQuery } from '@vueuse/core';
import { Modal } from 'bootstrap';

const { t } = useI18n();
const store = useDataStore();
const clickedObject = ref({})
const isMobile = useMediaQuery('(max-width: 768px');
let modalInstance = null;

const dataTableHeader = ref(null);

onMounted(() => {
  const modalElement = document.getElementById('dataModal');
  if (modalElement) {
    modalInstance = new Modal(modalElement);
  }
});

 // Sarakkeet:
 // Columns:
 const headerToKey = {
   "Tuotenimi": "tuotenimi",
   "Merkki ja malli": "merkki_ja_malli",
   "Kampus": "kampus",
   "Huone": "huone",
   "Vastuuhenkilö": "vastuuhenkilo",
   "Tilanne": "tilanne",
   "Product Name": "tuotenimi",
   "Brand and Model": "merkki_ja_malli",
   "Campus": "kampus",
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
   100, // Tuotenimi
   100, // Merkki ja malli
   60, // Kampus
   60, // Huone
   100, // Vastuuhenkilö
   100  // Tilanne
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
      const valA = (a[key] ?? '').toString().toLowerCase()
      const valB = (b[key] ?? '').toString().toLowerCase()

      const isEmptyA = valA === null || valA === '' || valA === undefined
      const isEmptyB = valB === null || valB === '' || valB === undefined

      // Put empty values last
      if (isEmptyA && !isEmptyB) return 1
      if (!isEmptyA && isEmptyB) return -1
      if (isEmptyA && isEmptyB) return 0

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

 const openOverlay = async (item) => {
   clickedObject.value = { ...item }
   await nextTick()
   const modalElement = document.getElementById('dataModal');
   const isAlreadyOpen = modalElement?.classList.contains('show');
   if (!isAlreadyOpen && modalInstance) {
     modalInstance.show();
   }
 }

 const handleUpdateItem = (updatedItem) => {
   store.updateObject(updatedItem);
   clickedObject.value = updatedItem
 }

 const handleDeleteItem = (itemId) => {
   store.deleteObject(itemId);
 }

 defineExpose({
   openOverlay,
   dataTableHeader
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
          <tr class="tuni-table-header" ref="dataTableHeader">
            <!-- Käydään läpi sarakeotsikot ja lisätään sort-indikaattori -->
            <!-- Go through the column headers and add a sort indicator -->
            <th class="tuni-table-header-cell" v-for="(key, index) in $tm('tableHeaders')" :key="key" :style="{ width: columnWidths[index] + 'px' }">
              <div class="sort-wrapper" @click.stop="toggleSort(key)" style="cursor: pointer;">
                <span class="header-text">{{ key }}</span>

                  <i :class="getSortClass(key)"></i>
              </div>
              <span class="resizer" @pointerdown="startResize($event, index)" role="separator" aria-orientation="vertical"></span>
            </th>
          </tr>
        </thead>

        <tbody>
          <tr v-for="(item, index) in displayedData" :key="index" :id="'datarow-'+index" @click="openOverlay(item)" data-bs-toggle="modal"
            data-bs-target="#dataModal">
            <td>
              {{ store.locale === 'fi' ? item.tuotenimi : item.tuotenimi_en }}
            </td>
            <td>
              {{ item.merkki_ja_malli }}
            </td>
            <td>
              {{ item.kampus }}
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
/*.sort-wrapper {
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

th,*/
/*td {
  padding: 8px;
  position: relative;
  text-align: left;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  border-bottom: var(--bs-border-width) var(--bs-border-style) var(--bs-border-color);
}*/

/*th {
  background-color: var(--bs-secondary-bg-subtle);
  position: sticky;
  top: calc(var(--header-height) + var(--actions-wrapper-height));
  z-index: 1;
}*/

/* Round top corners of header */
/*thead tr:first-child th:first-child {
  border-top-left-radius: 8px;
}

thead tr:first-child th:last-child {
  border-top-right-radius: 8px;
}*/

/* Round bottom corners of last row
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
*/
/* Round bottom corners of the last row
tbody tr:last-child td:first-child {
  border-bottom-left-radius: 8px;
}

tbody tr:last-child td:last-child {
  border-bottom-right-radius: 8px;
}*/

.sort-wrapper i {
  font-size: small;
}

.header-text {
  cursor: pointer;
}

.tuni-table-header-cell {
  position: relative;
  padding-right: 8px;
}

.resizer {
  position: absolute;
  top: 0;
  right: 0;
  width: 10px;
  height: 100%;
  cursor: col-resize;
  background: linear-gradient(90deg, rgba(0,0,0,0) 0%, rgba(0,0,0,0.04) 50%, rgba(0,0,0,0) 100%);
  transition: background .12s;
  z-index: 20;
}
.resizer:hover {
  background: rgba(0,0,0,0.08);
}
/* small visible line to hint the handle */
.resizer::after {
  content: '';
  position: absolute;
  top: 12%;
  bottom: 12%;
  right: 4px;
  width: 2px;
  background: rgba(0,0,0,0.18);
  border-radius: 1px;
}
</style>
