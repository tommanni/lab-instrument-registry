<script setup>
import { useAlertStore } from '@/stores/alert';
import { useContractStore } from '@/stores/contract';
import axios from 'axios';
import { computed, ref } from 'vue';
import { useI18n } from 'vue-i18n';

const i18n = useI18n();
const store = useContractStore();
const visible = ref(false)
const clickedObject = ref({})
const clickedUpdate = ref(false)
const alertStore = useAlertStore()
// DEMO
const columnWidths = ref([
  50,
  50,
  50,
  50,
  50
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

  const Data = computed(() => store.data);

const isMaintenanceDue = (dateStr) => {
  if (!dateStr) return false;
  const nextMaintenanceDate = new Date(dateStr);
  const today = new Date();
  // Erotetaan erotus päivissä:
  const diffInDays = (nextMaintenanceDate - today) / (1000 * 60 * 60 * 24);
  return diffInDays <= 30 && diffInDays >= 0;
};

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
    Object.entries(item).filter(([key]) => key !== 'id')
  );
}

const closeOverlay = () => {
  visible.value = false
  clickedUpdate.value = false
}

const updateData = () => {
  clickedUpdate.value = !clickedUpdate.value
}

const confirmUpdate = async () => {
  clickedUpdate.value = false
  visible.value = false
  console.log(JSON.parse(JSON.stringify(updateFormData.value)));
  await axios.put('/api/instruments/' + clickedObject.value.id + '/', JSON.parse(JSON.stringify(updateFormData.value)), {
      headers: {
        'Authorization': 'Token ' + document.cookie.split("; ").find((row) => row.startsWith("Authorization="))?.split("=")[1]
      }
    })
  alertStore.showAlert(0, i18n.t('message.on_paivitetty'))
  store.updateObject({ ...updateFormData.value, id: clickedObject.value.id })
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
          <button @click="updateData" class="btn btn-update">{{clickedUpdate ? $t('message.peruuta') : $t('message.muokkaa')}}</button>
          <button v-if="clickedUpdate" @click="confirmUpdate">{{ $t('message.paivita') }}</button>
        </div>
      </div>
    </div>
    
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
          <tr  v-for="(item, index) in Data" @click="openOverlay(item)" :key="index">
            <td>
              {{ item.tuotenimi }}
            </td>
            <td :class="{ urgent: isMaintenanceDue(item.seuraava_huolto) }">
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
.modal-buttons {
  margin-top: 15px;
  display: flex;
  justify-content: space-around;
}

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

</style>