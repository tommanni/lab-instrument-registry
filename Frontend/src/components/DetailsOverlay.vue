<script setup>
import { useAlertStore } from '@/stores/alert';
import { useDataStore } from '@/stores/data'
import axios from 'axios';
import { ref, watch } from 'vue';
import { useI18n } from 'vue-i18n';

const { t } = useI18n();
const store = useDataStore();
const alertStore = useAlertStore()

const props = defineProps({
  item: Object,
  visible: Boolean
});

const emit = defineEmits(['close', 'update-item', 'delete-item']);

const view = ref('details'); // details, edit, history
const showDeleteConfirmation = ref(false);
const updateFormData = ref({});
const instrumentHistory = ref([]);

// Map field names to their respective indices in fullHeaders array in messages.js
const fieldToIndexMap = {
  id: 0,
  tay_numero: 1,
  tuotenimi: 2,
  merkki_ja_malli: 3,
  sarjanumero: 4,
  yksikko: 5,
  kampus: 6,
  rakennus: 7,
  huone: 8,
  vastuuhenkilo: 9,
  toimituspvm: 10,
  toimittaja: 11,
  lisatieto: 12,
  vanha_sijainti: 13,
  tarkistettu: 14,
  huoltosopimus_loppuu: 15,
  edellinen_huolto: 16,
  seuraava_huolto: 17,
  tilanne: 18,
};

watch(() => props.item, (newItem) => {
  if (newItem && newItem.id) {
    view.value = 'details';
    updateFormData.value = Object.fromEntries(
      Object.entries(newItem).filter(([key]) => key !== 'id')
    );
    fetchHistory(newItem.id);
  }
}, { immediate: true, deep: true });

const fetchHistory = async (id) => {
  if (!id) return;
  try {
    const response = await axios.get(`/api/instruments/${id}/history/`, {
      headers: {
        'Authorization': 'Token ' + document.cookie.split("; ").find((row) => row.startsWith("Authorization="))?.split("=")[1]
      }
    });
    instrumentHistory.value = response.data.reverse();
  } catch (error) {
    console.error('Error fetching instrument history:', error);
  }
}


const closeOverlay = () => {
  emit('close');
  showDeleteConfirmation.value = false;
}

const confirmUpdate = async () => {
  try {
    await axios.put('/api/instruments/' + props.item.id + '/', JSON.parse(JSON.stringify(updateFormData.value)), {
        headers: {
          'Authorization': 'Token ' + document.cookie.split("; ").find((row) => row.startsWith("Authorization="))?.split("=")[1]
        }
      })
    alertStore.showAlert(0, t('message.on_paivitetty'))
    emit('update-item', { ...updateFormData.value, id: props.item.id });
    fetchHistory(props.item.id); // Refetch history after update
    view.value = 'details';
  } catch (error) {
    if (error.response && error.response.data && error.response.data.detail) {
      alertStore.showAlert(1, `${t('message.ei_paivitetty')} ${t('message.virhe')}: ${error.response.data.detail}`)
    } else {
      alertStore.showAlert(1, `${t('message.ei_paivitetty')}: ${t('message.tuntematon_virhe')}`)
    }
  }
}

const formatDate = (dateString) => {
  if (!dateString) return '';
  const date = new Date(dateString);
  return date.toLocaleString("fi-FI", {
    timeZone: "Europe/Helsinki",
    year: "numeric",
    month: "2-digit",
    day: "2-digit",
    hour: "2-digit",
    minute: "2-digit",
    hour12: false
  });
};

const confirmDelete = async () => {
  try {
    await axios.delete('/api/instruments/' + props.item.id + '/', {
        headers: {
          'Authorization': 'Token ' + document.cookie.split("; ").find((row) => row.startsWith("Authorization="))?.split("=")[1]
        }
      })
    alertStore.showAlert(0, `${props.item.tuotenimi} ${t('message.poistettu')}`)
    emit('delete-item', props.item.id);
    closeOverlay();
  } catch (error) {
    if (error.response && error.response.data && error.response.data.detail) {
      alertStore.showAlert(1, `${t('message.ei_poistettu')} ${t('message.virhe')}: ${error.response.data.detail}`)
    } else {
      alertStore.showAlert(1, `${t('message.ei_poistettu')}: ${t('message.tuntematon_virhe')}`)
    }
  }
}

</script>

<template>
  <div>
    <div v-if="visible" class="overlay-backdrop" @click="closeOverlay">
      <div @click.stop class="overlay-content">
        <button class="close-button" @click="closeOverlay">×</button>

        <!-- Details View -->
        <div v-if="view === 'details'">
          <h3 class="text-lg font-bold mb-2">{{$t('message.tiedot_nykyinen')}}</h3>
          <div class="data-container">
            <p><strong>{{ $tm('fullHeaders')[0] }}: </strong>{{ item.id }}</p>
            <p><strong>{{ $tm('fullHeaders')[1] }}: </strong>{{ item.tay_numero }}</p>
            <p><strong>{{ $tm('fullHeaders')[2] }}: </strong>{{ item.tuotenimi }}</p>
            <p><strong>{{ $tm('fullHeaders')[3] }}: </strong>{{ item.merkki_ja_malli }}</p>
            <p><strong>{{ $tm('fullHeaders')[4] }}: </strong>{{ item.sarjanumero }}</p>
            <p><strong>{{ $tm('fullHeaders')[5] }}: </strong>{{ item.yksikko }}</p>
            <p><strong>{{ $tm('fullHeaders')[6] }}: </strong>{{ item.kampus }}</p>
            <p><strong>{{ $tm('fullHeaders')[7] }}: </strong>{{ item.rakennus }}</p>
            <p><strong>{{ $tm('fullHeaders')[8] }}: </strong>{{ item.huone }}</p>
            <p><strong>{{ $tm('fullHeaders')[9] }}: </strong>{{ item.vastuuhenkilo }}</p>
            <p><strong>{{ $tm('fullHeaders')[10] }}: </strong>{{ item.toimituspvm }}</p>
            <p><strong>{{ $tm('fullHeaders')[11] }}: </strong>{{ item.toimittaja }}</p>
            <p><strong>{{ $tm('fullHeaders')[12] }}: </strong>{{ item.lisatieto }}</p>
            <p><strong>{{ $tm('fullHeaders')[13] }}: </strong>{{ item.vanha_sijainti }}</p>
            <p><strong>{{ $tm('fullHeaders')[14] }}: </strong>{{ item.tarkistettu }}</p>
            <p v-if="store.isLoggedIn"><strong>{{ $tm('fullHeaders')[15] }}: </strong>{{ item.huoltosopimus_loppuu }}</p>
            <p v-if="store.isLoggedIn"><strong>{{ $tm('fullHeaders')[16] }}: </strong>{{ item.edellinen_huolto }}</p>
            <p v-if="store.isLoggedIn"><strong>{{ $tm('fullHeaders')[17] }}: </strong>{{ item.seuraava_huolto }}</p>
            <p><strong>{{ $tm('fullHeaders')[18] }}: </strong>{{ item.tilanne }}</p>
          </div>
          <div class="buttons">
            <button v-if="store.isLoggedIn" @click="showDeleteConfirmation = true" class="btn btn-delete">{{$t('message.poista')}}</button>
            <button v-if="store.isLoggedIn" @click="view = 'history'" class="btn btn-history">{{$t('message.historia')}}</button>
            <button v-if="store.isLoggedIn" @click="view = 'edit'" class="btn btn-update">{{$t('message.muokkaa')}}</button>
          </div>
        </div>

        <!-- Edit View -->
        <div v-if="view === 'edit'">
          <h3 class="text-lg font-bold mb-2">{{$t('message.muokkaa_tietoja')}}</h3>
          <div class="data-container">
            <p><strong>{{ $tm('fullHeaders')[0] }}: </strong>{{ item.id }}</p>
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
            <button @click="confirmUpdate" class="btn btn-update2">{{ $t('message.paivita') }}</button>
            <button @click="view = 'details'" class="btn btn-cancel">{{$t('message.peruuta')}}</button>
          </div>
        </div>

        <!-- History View -->
        <div v-if="view === 'history'">
          <h3 class="text-lg font-bold mb-2">{{$t('message.muutoshistoria')}}</h3>
          <div class="history-details">
            <div v-for="record in instrumentHistory" :key="record.history_date" class="history-record">
              <p><strong>🗓️ {{ formatDate(record.history_date) }} — {{ record.history_type }}</strong></p>
              <p>👤 {{ record.history_user || 'Järjestelmä' }}</p>
              <hr>
              <ul>
                <li v-for="change in record.changes" :key="change.field">
                  • <strong>{{ $tm('fullHeaders')[fieldToIndexMap[change.field]] || change.field }}: </strong>{{ change.old }} <strong>{{ change.old ? "→" : "" }}</strong> {{ change.new ? change.new : "-" }}
                </li>
              </ul>
            </div>
          </div>
          <div class="buttons history-buttons">
            <button @click="view = 'details'" class="btn btn-cancel">{{$t('message.takaisin')}}</button>
          </div>
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
.btn-history {
  background-color: #0056b3;
  color: white;
}
.btn-history:hover {
  background-color: #4fa0f6;
}
.history-details {
  border-top: 1px solid #ccc;
  padding-top: 10px;
}
.history-record {
  margin-bottom: 15px;
  padding-bottom: 10px;
  border-bottom: 1px solid #eee;
}
.history-record ul {
  list-style-type: none;
  padding-left: 0;
}
.history-buttons {
  position: sticky;
  bottom: -2em;
  background-color: white;
  padding: 1em 2em;
  margin: 0 -2em;
  justify-content: center;
}
</style>
