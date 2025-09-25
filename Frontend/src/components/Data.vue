<script setup>
import { useAlertStore } from '@/stores/alert';
import { useDataStore } from '@/stores/data'
import axios from 'axios';
import { computed, ref } from 'vue';
import { useI18n } from 'vue-i18n';

const { t } = useI18n();
const store = useDataStore();
const visible = ref(false)
const clickedObject = ref({})
const showDeleteConfirmation = ref(false);
const clickedUpdate = ref(false)
const alertStore = useAlertStore()

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
const updateFormData = ref({
      tay_numero: '',
      tuotenimi: '',
      merkki_ja_malli: '',
      sarjanumero: '',
      yksikko: '',
      kampus: '',
      rakennus: '',
      huone: '',
      vastuuhenkilo: '',
      toimituspvm: '',
      toimittaja: '',
      lisatieto: '',
      vanha_sijainti: '',
      tarkistettu: '',
      huoltosopimus_loppuu: '',
      edellinen_huolto: '', 
      seuraava_huolto: '',
      tilanne: ''
  })

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
  console.log("opened: " + item["tuotenimi"]);
  clickedObject.value = {...item}
  visible.value = true
  updateFormData.value = Object.fromEntries(
    Object.entries(clickedObject.value).filter(([key]) => key !== 'id')
  );
}

const closeOverlay = () => {
  visible.value = false
  clickedUpdate.value = false
}

const confirmDelete = async (id) => {
  visible.value = false
  showDeleteConfirmation.value = false
  try {
    await axios.delete('/api/instruments/' + clickedObject.value.id + '/', {
        headers: {
          'Authorization': 'Token ' + document.cookie.split("; ").find((row) => row.startsWith("Authorization="))?.split("=")[1]
        }
      })
    alertStore.showAlert(0, `${clickedObject.value.tuotenimi} ${t('message.poistettu')}`)
    store.deleteObject(clickedObject.value.id)
  } catch (error) {
    if (error.response.data.detail != undefined) {
      alertStore.showAlert(1, `${t('message.ei_poistettu')} ${t('message.virhe')}: ${error.response.data.detail}`)
    } else {
      alertStore.showAlert(1, `${t('message.ei_poistettu')}: ${t('message.tuntematon_virhe')}`)
    }
    
  }
}

const updateData = () => {
  clickedUpdate.value = !clickedUpdate.value
}

const confirmUpdate = async () => {
  clickedUpdate.value = false
  visible.value = false
  console.log(JSON.parse(JSON.stringify(updateFormData.value)));
  try {
    await axios.put('/api/instruments/' + clickedObject.value.id + '/', JSON.parse(JSON.stringify(updateFormData.value)), {
        headers: {
          'Authorization': 'Token ' + document.cookie.split("; ").find((row) => row.startsWith("Authorization="))?.split("=")[1]
        }
      })
    alertStore.showAlert(0, t('message.on_paivitetty'))
    store.updateObject({ ...updateFormData.value, id: clickedObject.value.id })
  } catch (error) {
    // try to show the error message from the backend
    if (error.response.data.detail != undefined) {
      alertStore.showAlert(1, `${t('message.ei_paivitetty')} ${t('message.virhe')}: ${error.response.data.detail}`)
    } else {
      alertStore.showAlert(1, `${t('message.ei_paivitetty')}: ${t('message.tuntematon_virhe')}`)
    }
  }
}
</script>

<template>
  <div>
    <div v-if="visible" class="overlay-backdrop" @click="closeOverlay">
      <div @click.stop class="overlay-content">
        <button class="close-button" @click="closeOverlay">×</button>
        <h3 class="text-lg font-bold mb-2">{{$t('message.tiedot_nykyinen')}}</h3>
        <div v-if="!clickedUpdate" class="data-container">
          <p><strong>{{ $tm('fullHeaders')[0] }}: </strong>{{ clickedObject.id }}</p>
          <p><strong>{{ $tm('fullHeaders')[1] }}: </strong>{{ clickedObject.tay_numero }}</p>
          <p><strong>{{ $tm('fullHeaders')[2] }}: </strong>{{ clickedObject.tuotenimi }}</p>
          <p><strong>{{ $tm('fullHeaders')[3] }}: </strong>{{ clickedObject.merkki_ja_malli }}</p>
          <p><strong>{{ $tm('fullHeaders')[4] }}: </strong>{{ clickedObject.sarjanumero }}</p>
          <p><strong>{{ $tm('fullHeaders')[5] }}: </strong>{{ clickedObject.yksikko }}</p>
          <p><strong>{{ $tm('fullHeaders')[6] }}: </strong>{{ clickedObject.kampus }}</p>
          <p><strong>{{ $tm('fullHeaders')[7] }}: </strong>{{ clickedObject.rakennus }}</p>
          <p><strong>{{ $tm('fullHeaders')[8] }}: </strong>{{ clickedObject.huone }}</p>
          <p><strong>{{ $tm('fullHeaders')[9] }}: </strong>{{ clickedObject.vastuuhenkilo }}</p>
          <p><strong>{{ $tm('fullHeaders')[10] }}: </strong>{{ clickedObject.toimituspvm }}</p>
          <p><strong>{{ $tm('fullHeaders')[11] }}: </strong>{{ clickedObject.toimittaja }}</p>
          <p><strong>{{ $tm('fullHeaders')[12] }}: </strong>{{ clickedObject.lisatieto }}</p>
          <p><strong>{{ $tm('fullHeaders')[13] }}: </strong>{{ clickedObject.vanha_sijainti }}</p>
          <p><strong>{{ $tm('fullHeaders')[14] }}: </strong>{{ clickedObject.tarkistettu }}</p>
          <p v-if="store.isLoggedIn"><strong>{{ $tm('fullHeaders')[15] }}: </strong>{{ clickedObject.huoltosopimus_loppuu }}</p>
          <p v-if="store.isLoggedIn"><strong>{{ $tm('fullHeaders')[16] }}: </strong>{{ clickedObject.edellinen_huolto }}</p>
          <p v-if="store.isLoggedIn"><strong>{{ $tm('fullHeaders')[17] }}: </strong>{{ clickedObject.seuraava_huolto }}</p>
          <p><strong>{{ $tm('fullHeaders')[18] }}: </strong>{{ clickedObject.tilanne }}</p>
        </div>
        <div v-if="clickedUpdate" class="data-container">
          <p><strong>{{ $tm('fullHeaders')[0] }}: </strong>{{ clickedObject.id }}</p>
          <p><strong>{{ $tm('fullHeaders')[1] }}: </strong><input v-model="updateFormData['tay_numero']" type="text"></p>
          <p><strong>{{ $tm('fullHeaders')[2] }}: </strong><input v-model="updateFormData['tuotenimi']" type="text"></p>
          <p><strong>{{ $tm('fullHeaders')[3] }}: </strong><input type="text" v-model="updateFormData['merkki_ja_malli']"></p>
          <p><strong>{{ $tm('fullHeaders')[4] }}: </strong><input type="text" v-model="updateFormData['sarjanumero']"></p>
          <p><strong>{{ $tm('fullHeaders')[5] }}: </strong><input type="text" v-model="updateFormData['yksikko']"></p>
          <p><strong>{{ $tm('fullHeaders')[6] }}: </strong><input type="text" v-model="updateFormData['kampus']"></p>
          <p><strong>{{ $tm('fullHeaders')[7] }}: </strong><input type="text" v-model="updateFormData['rakennus']"></p>
          <p><strong>{{ $tm('fullHeaders')[8] }}: </strong><input type="text" v-model="updateFormData['huone']"></p>
          <p><strong>{{ $tm('fullHeaders')[9] }}: </strong><input type="text" v-model="updateFormData['vastuuhenkilo']"></p>
          <p><strong>{{ $tm('fullHeaders')[10] }}: </strong><input type="date" v-model="updateFormData['toimituspvm']"></p>
          <p><strong>{{ $tm('fullHeaders')[11] }}: </strong><input type="text" v-model="updateFormData['toimittaja']"></p>
          <p><strong>{{ $tm('fullHeaders')[12] }}: </strong><input type="text" v-model="updateFormData['lisatieto']"></p>
          <p><strong>{{ $tm('fullHeaders')[13] }}: </strong><input type="text" v-model="updateFormData['vanha_sijainti']"></p>
          <p><strong>{{ $tm('fullHeaders')[14] }}: </strong><input type="text" v-model="updateFormData['tarkistettu']"></p>
          <p><strong>{{ $tm('fullHeaders')[15] }}: </strong><input type="date" v-model="updateFormData['huoltosopimus_loppuu']"></p>
          <p><strong>{{ $tm('fullHeaders')[16] }}: </strong><input type="date" v-model="updateFormData['edellinen_huolto']"></p>
          <p><strong>{{ $tm('fullHeaders')[17] }}: </strong><input type="date" v-model="updateFormData['seuraava_huolto']"></p>
          <p><strong>{{ $tm('fullHeaders')[18] }}: </strong><input type="text" v-model="updateFormData['tilanne']"></p>
        </div>
        <div class="buttons">
          <button v-if="store.isLoggedIn" @click="showDeleteConfirmation = true" class="btn btn-delete">{{$t('message.poista')}}</button>
          <button v-if="clickedUpdate" @click="confirmUpdate" class="btn btn-update2">{{ $t('message.paivita') }}</button>
          <button v-if="store.isLoggedIn" @click="updateData" class="btn btn-update">{{clickedUpdate ? $t('message.peruuta') : $t('message.muokkaa')}}</button>
        </div>
      </div>
    </div>

    <div v-if="showDeleteConfirmation" class="overlay-backdrop">
      <div class="overlay-content">
        <p>{{$t('message.poisto_teksti')}}</p>
        <div class="modal-buttons">
          <button @click="confirmDelete" class="btn btn-delete">{{$t('message.kylla_poisto')}}</button>
          <button @click="showDeleteConfirmation = false" class="btn btn-cancel">{{$t('message.peruuta')}}</button>
        </div>
      </div>
    </div>
    
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
.overlay-backdrop {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background-color: rgba(0, 0, 0, 0.5);
  z-index: 1031;
}
.overlay-content {
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  background: #fff;
  padding: 2em;
  border-radius: 4px;
  box-shadow: 0 2px 10px rgba(0, 0, 0, 0.3);
  z-index: 1032;
  max-height: 80vh;
  overflow-y: auto;
  max-width: 90vw;
  width: 500px;
  word-wrap: break-word;
  overflow-wrap: break-word;
}
.data-container p {
  word-break: break-word;
  overflow-wrap: anywhere;
}
.overlay-content::-webkit-scrollbar {
  width: 8px;
}

.overlay-content::-webkit-scrollbar-thumb {
  background-color: #ccc;
  border-radius: 4px;
}
.close-button {
  position: absolute;
  top: 0.5em;
  right: 0.5em;
  background: transparent;
  border: none;
  font-size: 1.4rem;
  cursor: pointer;
  line-height: 1;
}
.close-button:hover {
  color: #b00;
}
.buttons {
  margin-top: 15px;
  display: flex;
  justify-content: space-between;
}
.btn {
  padding: 5px 10px;
  border: none;
  cursor: pointer;
  border-radius: 5px;
}
.btn-delete {
  background: #4E008E;
  color: white;
}
.btn-delete:hover {
  background-color: #ab9bcb;
}
.btn-cancel {
  background-color: rgb(158, 158, 158);
  color: white;
}
.btn-cancel:hover {
  background-color: #cacaca;
}
.btn-update {
  background: #cf286f;
  color: white;
}
.btn-update:hover {
  background-color: #F5A5C8;
}
.btn-update2 {
  background-color: rgb(0, 150, 0);
  color: white;
}
.btn-update2:hover {
  background-color: rgb(0, 234, 0);
}
.modal-buttons {
  margin-top: 15px;
  display: flex;
  justify-content: space-around;
}


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