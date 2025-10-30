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
  allowDelete: {
    type: Boolean,
    default: true
  }
});

const emit = defineEmits(['update-item', 'delete-item']);

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
  tuotenimi_en: 19,
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

const confirmUpdate = async () => {
  // Validate required fields
  formValidated.value = true;
  if (!updateFormData.value['tuotenimi']) {
    return; // Don't save if validation fails
  }

  try {
    const response = await axios.put(
      '/api/instruments/' + props.item.id + '/', 
      JSON.parse(JSON.stringify(updateFormData.value)), 
      { withCredentials: true }
    )
    alertStore.showAlert(0, t('message.on_paivitetty'))

    emit('update-item', response.data);

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
                      <label for="product-name-en">{{ tm('fullHeaders')[19] }}</label>
                      <input id="product-name-en" class="form-control" :disabled="view != 'edit'"
                        v-model="updateFormData['tuotenimi_en']" type="text">
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
                <button v-if="view === 'details'" class="btn btn-secondary me-2" data-bs-dismiss="modal">
                  {{ t('message.takaisin') }}
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
                <button v-if="store.isLoggedIn && view === 'details' && allowDelete" class="btn btn-danger me-2" data-bs-toggle="modal"
                  data-bs-target="#deleteConfirmModal">
                  {{ t('message.poista') }}
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
  </div>
</template>

<style scoped>

.data-container p {
  word-break: break-word;
  overflow-wrap: anywhere;
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
</style>
