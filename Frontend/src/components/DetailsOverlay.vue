<script setup>
import { useAlertStore } from '@/stores/alert';
import { useDataStore } from '@/stores/data'
import axios from 'axios';
import { ref, watch, onMounted } from 'vue';
import { useI18n } from 'vue-i18n';
import { Modal } from 'bootstrap';

const { t, tm } = useI18n();
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
const formValidated = ref(false);
const updateIsDisabled = ref(true);

// Watch for changes in updateFormData to enable/disable update button
watch(updateFormData, (newData) => {
  if (!props.item) {
    updateIsDisabled.value = true;
    return;
  }
  
  // Compare each field in updateFormData with original item
  updateIsDisabled.value = Object.keys(newData).every(key => {
    const originalValue = props.item[key]?.toString() || '';
    const newValue = newData[key]?.toString() || '';
    return originalValue === newValue;
  });
}, { deep: true });

const dataModal = ref(null);
const deleteModal = ref(null);


onMounted(() => {
  const dataModalElement = document.getElementById('dataModal');
  const deleteModalElement = document.getElementById('deleteConfirmModal');

  dataModal.value = new Modal(dataModalElement, {
    backdrop: 'static',
    keyboard: true
  });
  deleteModal.value = new Modal(deleteModalElement, {
    backdrop: 'static',
    keyboard: false
  });

  // Reset validation state when modal is closed
  dataModalElement.addEventListener('hidden.bs.modal', () => {
    formValidated.value = false;
  });
});

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
      withCredentials: true
    });
    instrumentHistory.value = response.data.reverse();
  } catch (error) {
    console.error('Error fetching instrument history:', error);
  }
}


const resetFormData = () => {
  if (props.item) {
    updateFormData.value = Object.fromEntries(
      Object.entries(props.item).filter(([key]) => key !== 'id')
    );
  }
};

const cancelEdit = () => {
  resetFormData();
  formValidated.value = false;
  view.value = 'details';
};

const closeOverlay = () => {
  if (dataModal.value) {
    dataModal.value.hide();
  }
  emit('close');
  showDeleteConfirmation.value = false;
}

const confirmUpdate = async () => {
  // Validate required fields
  formValidated.value = true;
  if (!updateFormData.value['tuotenimi']) {
    return; // Don't save if validation fails
  }

  try {
    await axios.put('/api/instruments/' + props.item.id + '/', JSON.parse(JSON.stringify(updateFormData.value)), {
      withCredentials: true
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
      withCredentials: true
    })
    alertStore.showAlert(0, `${props.item.tuotenimi} ${t('message.poistettu')}`)
    emit('delete-item', props.item.id);
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
  <div class="instrument-data-wrapper">

    <teleport to="body">
      <div class="modal fade" id="dataModal" tabindex="-1" aria-labelledby="dataModalLabel" aria-hidden="true">
        <div class="modal-dialog modal-dialog-centered modal-lg">
          <div class="modal-content">
            <div class="modal-header">
              <h5 class="modal-title" id="dataModalLabel">{{ view !== 'history' ?
                t('message.tiedot_nykyinen') : t('message.muutoshistoria') }}</h5>
              <button type="button" class="btn-close" data-bs-dismiss="modal" aria-label="Close"></button>
            </div>
            <div class="modal-body">
              <form @submit.prevent="confirmUpdate" :class="{'was-validated': formValidated}" class="container compact-form" novalidate
                v-if="view !== 'history'">
                <div class="row row-cols-2">
                  <div class="col d-flex flex-column gap-3">
                    <!-- First column fields -->
                    <div class="form-field-wrapper">
                      <label for="tay-no">{{ tm('fullHeaders')[1] }}</label>
                      <input id="tay-no" v-model="updateFormData['tay_numero']" class="form-control" type="text"
                        :disabled="view != 'edit'">
                    </div>
                    <div class="form-field-wrapper">
                      <label for="product-name">{{ tm('fullHeaders')[2] }} <span v-if="view === 'edit'" class="text-danger">*</span></label>
                      <input id="product-name" class="form-control" :disabled="view != 'edit'"
                        v-model="updateFormData['tuotenimi']" type="text" :required="view === 'edit'">
                    </div>
                    <div class="form-field-wrapper">
                      <label for="product-model">{{ tm('fullHeaders')[3] }}</label>
                      <input id="product-model" class="form-control" :disabled="view != 'edit'"
                        v-model="updateFormData['merkki_ja_malli']">
                    </div>
                    <div class="form-field-wrapper">
                      <label for="unit">{{ tm('fullHeaders')[5] }}</label>
                      <input id="unit" class="form-control" :disabled="view != 'edit'"
                        v-model="updateFormData['yksikko']">
                    </div>
                    <div class="form-field-wrapper">
                      <label for="campus">{{ tm('fullHeaders')[6] }}</label>
                      <input id="campus" class="form-control" :disabled="!(view == 'edit')"
                        v-model="updateFormData['kampus']">
                    </div>
                    <div class="form-field-wrapper">
                      <label for="responsible-person">{{ tm('fullHeaders')[9] }}</label>
                      <input id="responsible-person" class="form-control" :disabled="view != 'edit'"
                        v-model="updateFormData['vastuuhenkilo']">
                    </div>
                    <div class="form-field-wrapper">
                      <label for="deliverydate">{{ tm('fullHeaders')[10] }}</label>
                      <input id="deliverydate" class="form-control" :disabled="view != 'edit'" type="date"
                        v-model="updateFormData['toimituspvm']">
                    </div>
                    <div class="form-field-wrapper">
                      <label for="prev-maintenance">{{ tm('fullHeaders')[16] }}</label>
                      <input id="prev-maintenance" class="form-control" :disabled="view != 'edit'" type="date"
                        v-model="updateFormData['edellinen_huolto']">
                    </div>
                  </div>
                  <div class="col d-flex flex-column gap-3">
                    <!-- Second column fields -->
                    <div class="form-field-wrapper">
                      <label for="product-serialno">{{ tm('fullHeaders')[4] }}</label>
                      <input id="product-serialno" class="form-control" :disabled="view != 'edit'"
                        v-model="updateFormData['sarjanumero']">
                    </div>
                    <div class="form-field-wrapper">
                      <label for="building">{{ tm('fullHeaders')[7] }}</label>
                      <input id="building" class="form-control" :disabled="view != 'edit'"
                        v-model="updateFormData['rakennus']">
                    </div>
                    <div class="form-field-wrapper">
                      <label for="room">{{ tm('fullHeaders')[8] }}</label>
                      <input id="room" class="form-control" :disabled="view != 'edit'"
                        v-model="updateFormData['huone']">
                    </div>
                    <div class="form-field-wrapper">
                      <label for="supplier">{{ tm('fullHeaders')[11] }}</label>
                      <input id="supplier" class="form-control" :disabled="view != 'edit'"
                        v-model="updateFormData['toimittaja']">
                    </div>
                    <div class="form-field-wrapper">
                      <label for="contract-ends">{{ tm('fullHeaders')[15] }}</label>
                      <input id="contract-ends" class="form-control" :disabled="view != 'edit'" type="date"
                        v-model="updateFormData['huoltosopimus_loppuu']">
                    </div>
                    <div class="form-field-wrapper">
                      <label for="next-maintenance">{{ tm('fullHeaders')[17] }}</label>
                      <input id="next-maintenance" class="form-control" :disabled="view != 'edit'" type="date"
                        v-model="updateFormData['seuraava_huolto']">
                    </div>
                    <div class="form-field-wrapper">
                      <label for="status">{{ tm('fullHeaders')[18] }}</label>
                      <input id="status" class="form-control" :disabled="view != 'edit'"
                        v-model="updateFormData['tilanne']">
                    </div>
                  </div>
                  <div class="mt-3">
                    <div class="form-field-wrapper">
                      <label for="footnote">{{ tm('fullHeaders')[12] }}</label>
                      <textarea id="footnote" class="form-control" :disabled="view != 'edit'"
                        v-model="updateFormData['lisatieto']"></textarea>
                    </div>
                  </div>
                </div>
              </form>
              <!--Change history-->
              <div v-if="view === 'history'" class="container">
                <div class="history-details">
                  <div v-for="record in instrumentHistory" :key="record.history_date" class="history-record">
                    <p><strong>🗓️ {{ formatDate(record.history_date) }} — {{ record.history_type }}</strong></p>
                    <p>👤 {{ record.history_user || t('message.jarjestelma') }}</p>
                    <hr>
                    <ul>
                      <li v-for="change in record.changes" :key="change.field">
                        • <strong>{{ tm('fullHeaders')[fieldToIndexMap[change.field]] || change.field }}: </strong>{{
                          change.old }} <strong>{{ change.old ? "→" : "" }}</strong> {{ change.new ? change.new : "-" }}
                      </li>
                    </ul>
                  </div>
                </div>
              </div>
            </div>




            <!--Modal footer-->
            <div class="modal-footer justify-content-between">
              <div>
                <button v-if="store.isLoggedIn && view !== 'history'" class="btn btn-danger me-2" data-bs-toggle="modal"
                  data-bs-target="#deleteConfirmModal">
                  {{ t('message.poista') }}
                </button>
                <button v-if="store.isLoggedIn && view === 'details'" @click="view = 'history'"
                  class="btn btn-outline-info">{{
                    t('message.historia') }}</button>
                <button v-if="view === 'history'" @click="view = 'details'" class="btn btn-secondary">
                  {{ t('message.takaisin') }}
                </button>
              </div>

              <div>
                <button
                  v-if="store.isLoggedIn && view == 'edit'"
                  @click="cancelEdit"
                  class="btn btn-secondary me-2"
                >
                  {{t('message.peruuta') }}
                </button>
                <button
                  class="btn btn-primary"
                  v-if="store.isLoggedIn && view == 'details'"
                  @click="view = 'edit'"
                >
                  {{ t('message.muokkaa') }}
                </button>
                <button :disabled="updateIsDisabled" v-if="view === 'edit'" @click="confirmUpdate" class="btn btn-primary">
                  {{ t('message.paivita')}}
                </button>
              </div>
              

            </div>
          </div>
        </div>
      </div>

      <div class="modal fade" id="deleteConfirmModal" tabindex="-1" aria-labelledby="deleteConfirmModalLabel"
        aria-hidden="true">
        <div class="modal-dialog modal-dialog-centered">
          <div class="modal-content">
            <div class="modal-body">
              <p>{{ t('message.poisto_teksti') }}</p>
            </div>
            <div class="modal-footer">
              <button @click="confirmDelete" data-bs-dismiss="modal" class="btn btn-danger">{{
                t('message.kylla_poisto') }}</button>
              <button type="button" class="btn btn-secondary" data-bs-dismiss="modal" data-bs-toggle="modal"
                data-bs-target="#dataModal">{{
                  t('message.peruuta')
                }}</button>
            </div>
          </div>
        </div>
      </div>
    </teleport>















    <!--<div v-if="visible" class="overlay-backdrop" @click="closeOverlay">
        <div @click.stop class="overlay-content">
          <button class="close-button" @click="closeOverlay">×</button>





          <!-- Details View 
        <div v-if="view === 'details'">
          <h3 class="text-lg font-bold mb-2">{{t('message.tiedot_nykyinen')}}</h3>
          <div class="data-container">
            <p><strong>{{ tm('fullHeaders')[0] }}: </strong>{{ item.id }}</p>
            <p><strong>{{ tm('fullHeaders')[1] }}: </strong>{{ item.tay_numero }}</p>
            <p><strong>{{ tm('fullHeaders')[2] }}: </strong>{{ item.tuotenimi }}</p>
            <p><strong>{{ tm('fullHeaders')[3] }}: </strong>{{ item.merkki_ja_malli }}</p>
            <p><strong>{{ tm('fullHeaders')[4] }}: </strong>{{ item.sarjanumero }}</p>
            <p><strong>{{ tm('fullHeaders')[5] }}: </strong>{{ item.yksikko }}</p>
            <p><strong>{{ tm('fullHeaders')[6] }}: </strong>{{ item.kampus }}</p>
            <p><strong>{{ tm('fullHeaders')[7] }}: </strong>{{ item.rakennus }}</p>
            <p><strong>{{ tm('fullHeaders')[8] }}: </strong>{{ item.huone }}</p>
            <p><strong>{{ tm('fullHeaders')[9] }}: </strong>{{ item.vastuuhenkilo }}</p>
            <p><strong>{{ tm('fullHeaders')[10] }}: </strong>{{ item.toimituspvm }}</p>
            <p><strong>{{ tm('fullHeaders')[11] }}: </strong>{{ item.toimittaja }}</p>
            <p><strong>{{ tm('fullHeaders')[12] }}: </strong>{{ item.lisatieto }}</p>
            <p><strong>{{ tm('fullHeaders')[13] }}: </strong>{{ item.vanha_sijainti }}</p>
            <p><strong>{{ tm('fullHeaders')[14] }}: </strong>{{ item.tarkistettu }}</p>
            <p v-if="store.isLoggedIn"><strong>{{ tm('fullHeaders')[15] }}: </strong>{{ item.huoltosopimus_loppuu }}</p>
            <p v-if="store.isLoggedIn"><strong>{{ tm('fullHeaders')[16] }}: </strong>{{ item.edellinen_huolto }}</p>
            <p v-if="store.isLoggedIn"><strong>{{ tm('fullHeaders')[17] }}: </strong>{{ item.seuraava_huolto }}</p>
            <p><strong>{{ tm('fullHeaders')[18] }}: </strong>{{ item.tilanne }}</p>
          </div>
          <div class="buttons">
            <button v-if="store.isLoggedIn" @click="showDeleteConfirmation = true" class="btn btn-delete">{{t('message.poista')}}</button>
            <button v-if="store.isLoggedIn" @click="view = 'history'" class="btn btn-history">{{t('message.historia')}}</button>
            <button v-if="store.isLoggedIn" @click="view = 'edit'" class="btn btn-update">{{t('message.muokkaa')}}</button>
          </div>
        </div>-->

    <!-- Edit View 
        <div v-if="view === 'edit'">
          <h3 class="text-lg font-bold mb-2">{{t('message.muokkaa_tietoja')}}</h3>
          <div class="data-container">
            <p><strong>{{ tm('fullHeaders')[0] }}: </strong>{{ item.id }}</p>
            <p><strong>{{ tm('fullHeaders')[1] }}: </strong><input v-model="updateFormData['tay_numero']" type="text"></p>
            <p><strong>{{ tm('fullHeaders')[2] }}: </strong><input v-model="updateFormData['tuotenimi']" type="text"></p>
            <p><strong>{{ tm('fullHeaders')[3] }}: </strong><input type="text" v-model="updateFormData['merkki_ja_malli']"></p>
            <p><strong>{{ tm('fullHeaders')[4] }}: </strong><input type="text" v-model="updateFormData['sarjanumero']"></p>
            <p><strong>{{ tm('fullHeaders')[5] }}: </strong><input type="text" v-model="updateFormData['yksikko']"></p>
            <p><strong>{{ tm('fullHeaders')[6] }}: </strong><input type="text" v-model="updateFormData['kampus']"></p>
            <p><strong>{{ tm('fullHeaders')[7] }}: </strong><input type="text" v-model="updateFormData['rakennus']"></p>
            <p><strong>{{ tm('fullHeaders')[8] }}: </strong><input type="text" v-model="updateFormData['huone']"></p>
            <p><strong>{{ tm('fullHeaders')[9] }}: </strong><input type="text" v-model="updateFormData['vastuuhenkilo']"></p>
            <p><strong>{{ tm('fullHeaders')[10] }}: </strong><input type="date" v-model="updateFormData['toimituspvm']"></p>
            <p><strong>{{ tm('fullHeaders')[11] }}: </strong><input type="text" v-model="updateFormData['toimittaja']"></p>
            <p><strong>{{ tm('fullHeaders')[12] }}: </strong><input type="text" v-model="updateFormData['lisatieto']"></p>
            <p><strong>{{ tm('fullHeaders')[13] }}: </strong><input type="text" v-model="updateFormData['vanha_sijainti']"></p>
            <p><strong>{{ tm('fullHeaders')[14] }}: </strong><input type="text" v-model="updateFormData['tarkistettu']"></p>
            <p><strong>{{ tm('fullHeaders')[15] }}: </strong><input type="date" v-model="updateFormData['huoltosopimus_loppuu']"></p>
            <p><strong>{{ tm('fullHeaders')[16] }}: </strong><input type="date" v-model="updateFormData['edellinen_huolto']"></p>
            <p><strong>{{ tm('fullHeaders')[17] }}: </strong><input type="date" v-model="updateFormData['seuraava_huolto']"></p>
            <p><strong>{{ tm('fullHeaders')[18] }}: </strong><input type="text" v-model="updateFormData['tilanne']"></p>
          </div>
          <div class="buttons">
            <button @click="confirmUpdate" class="btn btn-update2">{{ t('message.paivita') }}</button>
            <button @click="view = 'details'" class="btn btn-cancel">{{t('message.peruuta')}}</button>
          </div>
        </div>-->

    <!-- History View 
        <div v-if="view === 'history'">
          <h3 class="text-lg font-bold mb-2">{{t('message.muutoshistoria')}}</h3>
          <div class="history-details">
            <div v-for="record in instrumentHistory" :key="record.history_date" class="history-record">
              <p><strong>🗓️ {{ formatDate(record.history_date) }} — {{ record.history_type }}</strong></p>
              <p>👤 {{ record.history_user || 'Järjestelmä' }}</p>
              <hr>
              <ul>
                <li v-for="change in record.changes" :key="change.field">
                  • <strong>{{ tm('fullHeaders')[fieldToIndexMap[change.field]] || change.field }}: </strong>{{ change.old }} <strong>{{ change.old ? "→" : "" }}</strong> {{ change.new ? change.new : "-" }}
                </li>
              </ul>
            </div>
          </div>
          <div class="buttons history-buttons">
            <button @click="view = 'details'" class="btn btn-cancel">{{t('message.takaisin')}}</button>
          </div>
        </div>

        </div>
      </div>

      <div v-if="showDeleteConfirmation" class="overlay-backdrop">
        <div class="overlay-content">
          <p>{{t('message.poisto_teksti')}}</p>
          <div class="modal-buttons">
            <button @click="confirmDelete" class="btn btn-delete">{{t('message.kylla_poisto')}}</button>
            <button @click="showDeleteConfirmation = false" class="btn btn-cancel">{{t('message.peruuta')}}</button>
          </div>
        </div>
      </div>-->
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
  z-index: 1060;
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
  min-height: 710px;
  max-height: 710px;
  overflow-y: auto;
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

/* Compact form styling */
.compact-form {
  gap: 0.5rem;
}

.compact-form label {
  margin-bottom: 0.2rem;
  font-size: 0.9rem;
}

/* Remove green validation styling, keep only red for errors */
.compact-form .form-control:valid {
  border-color: #dee2e6;
  background-image: none;
}

.compact-form .form-control:valid:focus {
  border-color: #86b7fe;
  box-shadow: 0 0 0 0.25rem rgba(13, 110, 253, 0.25);
}

.compact-form .form-control:invalid {
  border-color: #dc3545;
  background-image: none;
}

.compact-form .form-control:invalid:focus {
  border-color: #dc3545;
  box-shadow: 0 0 0 0.25rem rgba(220, 53, 69, 0.25);
}

/* Reduce form control padding */
.compact-form .form-control {
  padding: 0.375rem 0.75rem;
  font-size: 0.9rem;
}

/* Reduce modal body padding */
.modal-body {
  padding: 1rem 1.5rem;
}
</style>
