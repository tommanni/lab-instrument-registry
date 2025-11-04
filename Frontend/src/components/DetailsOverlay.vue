<script setup>
import { useAlertStore } from '@/stores/alert';
import { useDataStore } from '@/stores/data'
import axios from 'axios';
import { ref, watch, onMounted, computed } from 'vue';
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
const isUpdating = ref(false);
const pendingUpdatePayload = ref(null);
const pendingDuplicateCount = ref(0);
const showDuplicateConfirm = computed(() => Boolean(pendingUpdatePayload.value));

const duplicateCount = computed(() => {
  if (!store.isInitialized || !props.item) return 0
  const targetName = (updateFormData.value.tuotenimi || '').trim().toLowerCase()
  const newTranslation = updateFormData.value.tuotenimi_en
  return (store.originalData || []).filter(inst => {
    return inst.id !== props.item.id &&
           (inst.tuotenimi || '').trim().toLowerCase() === targetName &&
           inst.tuotenimi_en !== newTranslation
  }).length
})

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
    pendingUpdatePayload.value = null;
    pendingDuplicateCount.value = 0;
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

  if (isUpdating.value) {
    return
  }

  if (!store.isInitialized) {
  console.warn("Store not initialized yet.")
  return
}

  const originalName = ((props.item && props.item.tuotenimi) ? props.item.tuotenimi : '').trim().toLowerCase()
  const currentName = (updateFormData.value.tuotenimi || '').trim().toLowerCase()
  const tuotenimiUnchanged = originalName === currentName
  const englishChanged = props.item ? updateFormData.value.tuotenimi_en !== props.item.tuotenimi_en : false

  const payload = JSON.parse(JSON.stringify(updateFormData.value))
  if (tuotenimiUnchanged && englishChanged && duplicateCount.value > 0) {
    pendingUpdatePayload.value = payload
    pendingDuplicateCount.value = duplicateCount.value
    return
  }

  await performUpdate(payload)
}

const proceedDuplicateUpdate = async () => {
  if (isUpdating.value || !pendingUpdatePayload.value) {
    return
  }

  const payload = {
    ...pendingUpdatePayload.value,
    update_duplicates: true
  }
  pendingUpdatePayload.value = null
  await performUpdate(payload)
}

const updateOnlyCurrent = async () => {
  if (isUpdating.value) {
    return
  }

  if (!pendingUpdatePayload.value) {
    pendingDuplicateCount.value = 0
    return
  }

  const payload = { ...pendingUpdatePayload.value }
  pendingUpdatePayload.value = null
  await performUpdate(payload)
}

const performUpdate = async (payload) => {
  if (isUpdating.value) {
    return
  }

  isUpdating.value = true
  try {
    const response = await axios.put(
      '/api/instruments/' + props.item.id + '/', 
      payload, 
      { withCredentials: true }
    )
    alertStore.showAlert(0, t('message.on_paivitetty'))

    emit('update-item', response.data);

    if (payload.update_duplicates) {
      store.updateDuplicateTuotenimiEN(
        updateFormData.value.tuotenimi,
        response.data.tuotenimi_en
      )
    }

    fetchHistory(props.item.id); // Refetch history after update
    view.value = 'details';
    pendingDuplicateCount.value = 0
  } catch (error) {
    if (error.response && error.response.data && error.response.data.detail) {
      alertStore.showAlert(1, `${t('message.ei_paivitetty')} ${t('message.virhe')}: ${error.response.data.detail}`)
    } else {
      alertStore.showAlert(1, `${t('message.ei_paivitetty')}: ${t('message.tuntematon_virhe')}`)
    }
  }
  finally {
    isUpdating.value = false
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

const cancelDuplicateUpdate = () => {
  pendingUpdatePayload.value = null
  pendingDuplicateCount.value = 0
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
              <button
                type="button"
                class="btn-close"
                data-bs-dismiss="modal"
                aria-label="Close"
                :disabled="showDuplicateConfirm || isUpdating"
              ></button>
            </div>
            <div class="modal-body position-relative">
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
                  <div
                    v-for="record in instrumentHistory"
                    :key="record.history_date"
                    class="card history-card border border-secondary bg-secondary-subtle mb-2"
                  >
                    <div class="card-body">
                      <div class="d-flex flex-wrap align-items-center justify-content-between gap-3">
                        <div class="d-flex flex-wrap align-items-center gap-2">
                          <span class="fw-semibold">{{ formatDate(record.history_date) }}</span>
                          <span class="text-muted small">
                            {{ record.history_user || t('message.jarjestelma') }}
                          </span>
                        </div>
                        <span class="badge text-uppercase bg-primary">{{ record.history_type }}</span>
                      </div>
                    </div>
                    <ul class="list-group list-group-flush">
                      <li
                        v-for="change in record.changes"
                        :key="change.field"
                        class="list-group-item small bg-body"
                      >
                        <span class="fw-semibold">
                          {{ tm('fullHeaders')[fieldToIndexMap[change.field]] || change.field }}:
                        </span>
                        <template v-if="record.history_type !== 'Created'">
                          <span class="text-muted">
                            {{ change.old || '-' }}
                          </span>
                          <span class="mx-1 text-muted" v-if="change.old || change.new">→</span>
                        </template>
                        <span>{{ change.new || '-' }}</span>
                      </li>
                    </ul>
                  </div>
                </div>
              </div>

              <transition name="fade">
                <div
                  v-if="showDuplicateConfirm"
                  class="duplicate-confirm-overlay d-flex align-items-center justify-content-center"
                  role="dialog"
                  aria-modal="true"
                >
                  <div class="duplicate-confirm-card bg-white p-4 w-100">
                    <h5 class="mb-3">{{ t('message.muutosvahvistus') }}</h5>
                    <p class="mb-2">{{ t('message.loytyi_duplikaatteja', { count: pendingDuplicateCount }) }}</p>
                    <p class="text-muted small mb-4">{{ t('message.paivita_duplikaatit_kysymys') }}</p>
                    <div class="d-flex justify-content-end gap-2">
                      <button type="button" class="btn btn-secondary border" @click="cancelDuplicateUpdate" :disabled="isUpdating">
                        {{ t('message.peru_päivitys') }}
                      </button>
                      <button type="button" class="btn btn-light border" @click="updateOnlyCurrent" :disabled="isUpdating">
                        {{ t('message.päivitä_yksi') }}
                      </button>
                      <button type="button" class="btn btn-primary" @click="proceedDuplicateUpdate" :disabled="isUpdating">
                        <span
                          v-if="isUpdating"
                          class="spinner-border spinner-border-sm me-2"
                          role="status"
                          aria-hidden="true"
                        ></span>
                        {{ isUpdating ? t('message.paivitetaan') : t('message.kylla_paivita') }}
                      </button>
                    </div>
                  </div>
                </div>
              </transition>
            </div>
            <!--Modal footer-->
            <div class="modal-footer justify-content-between">
              <div>
                <button
                  v-if="view === 'details'"
                  class="btn btn-secondary me-2"
                  data-bs-dismiss="modal"
                  :disabled="showDuplicateConfirm || isUpdating"
                >
                  {{ t('message.takaisin') }}
                </button>
                <button
                  v-if="store.isLoggedIn && view === 'details'"
                  @click="view = 'history'"
                  class="btn btn-outline-info"
                  :disabled="showDuplicateConfirm || isUpdating"
                >{{
                    t('message.historia') }}</button>
                <button
                  v-if="view === 'history'"
                  @click="view = 'details'"
                  class="btn btn-secondary"
                  :disabled="showDuplicateConfirm || isUpdating"
                >
                  {{ t('message.takaisin') }}
                </button>
              </div>

              <div>
                <button
                  v-if="store.isLoggedIn && view == 'edit'"
                  @click="cancelEdit"
                  class="btn btn-secondary me-2"
                  :disabled="showDuplicateConfirm || isUpdating"
                >
                  {{t('message.peruuta') }}
                </button>
                <button
                  v-if="store.isLoggedIn && view === 'details' && allowDelete"
                  class="btn btn-danger me-2"
                  data-bs-toggle="modal"
                  data-bs-target="#deleteConfirmModal"
                  :disabled="showDuplicateConfirm || isUpdating"
                >
                  {{ t('message.poista') }}
                </button>
                <button
                  class="btn btn-primary"
                  v-if="store.isLoggedIn && view == 'details'"
                  @click="view = 'edit'"
                  :disabled="showDuplicateConfirm || isUpdating"
                >
                  {{ t('message.muokkaa') }}
                </button>
                <button
                  class="btn btn-primary"
                  v-if="view === 'edit'"
                  :disabled="updateIsDisabled || isUpdating"
                  @click="confirmUpdate"
                >
                  <span
                    v-if="isUpdating"
                    class="spinner-border spinner-border-sm me-2"
                    role="status"
                    aria-hidden="true"
                  ></span>
                  {{ isUpdating ? t('message.paivitetaan') : t('message.paivita')}}
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
  max-height: 60vh;
  overflow-y: auto;
  padding-top: 0.5rem;
}

.history-card {
  border-radius: 0.35rem;
  overflow: hidden;
}

.history-card .card-body {
  padding: 0.75rem 1rem;
}

.history-card .list-group-item {
  border-color: rgba(0, 0, 0, 0.05);
  background-color: var(--bs-body-bg);
  padding: 0.5rem 1rem;
}

.duplicate-confirm-overlay {
  position: absolute;
  inset: 0;
  padding: 1.5rem;
  z-index: 1050;
  pointer-events: auto;
}

.duplicate-confirm-card {
  max-width: 420px;
  margin: 0 auto;
  border-radius: 6px;
  border: 1px solid rgba(0, 0, 0, 0.08);
  box-shadow: 0 2px 10px rgba(0, 0, 0, 0.3);
  pointer-events: auto;
}

.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.18s ease;
}

.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}

</style>
