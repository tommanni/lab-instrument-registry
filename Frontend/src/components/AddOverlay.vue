<script setup>
import axios from 'axios'
import { ref, onMounted } from 'vue'
import { useDataStore } from '@/stores/data'
import { useAlertStore } from '@/stores/alert'
import { useI18n } from 'vue-i18n';
import { Modal } from 'bootstrap';

const i18n = useI18n();
const store = useDataStore()
const showOverlay = ref(false)
const alertStore = useAlertStore()
const emit = defineEmits(['new-instrument-added'])
const formValidated = ref(false)
let modalInstance = null

onMounted(() => {
  const modalElement = document.getElementById('addModal')
  if (modalElement) {
    modalInstance = new Modal(modalElement)

    // Reset validation state when modal is closed
    modalElement.addEventListener('hidden.bs.modal', () => {
      formValidated.value = false
    })
  }
})

// Factory function to create base form data (core instrument fields only)
// Funktio, joka luo peruslomakedata (vain ydinlaitteen kentät)
const createBaseFormData = () => ({
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
  tilanne: "Saatavilla"
})

// Factory function to create form data with maintenance fields for reset
// Funktio, joka luo lomakedata huoltokentillä nollausta varten
const createFormDataWithMaintenance = () => ({
  ...createBaseFormData(),
  huoltosopimus_loppuu: '',
  edellinen_huolto: '',
  seuraava_huolto: ''
})

// Lomakedata, joka tallennetaan
// Form data that will be saved
const formData = ref(createBaseFormData())


const closeOverlay = () => {
  showOverlay.value = false
}

const emptyForm = () => {
  formData.value = createFormDataWithMaintenance()
}

const saveData = async () => {
  /*
    attempt to save the instrument
    alert the user whether it succeeded
  */

  // Validate required fields
  formValidated.value = true
  if (!formData.value.tuotenimi || !formData.value.merkki_ja_malli || !formData.value.kampus) {
    return // Don't save if validation fails
  }

  try {
    // send the data without any empty fields
    var dataToSend = {};
    for (const key in formData.value) {
      if (formData.value[key] !== "") {
        dataToSend[key] = formData.value[key]
      }
    }

    const response = await axios.post('/api/instruments/', dataToSend, {withCredentials: true})

    alertStore.showAlert(0, `${dataToSend.tuotenimi} ${i18n.t('message.lisatty')}`)
    const savedItem = response.data
    store.addObject(savedItem)
    emit('new-instrument-added', savedItem)

    // Close modal only on successful save
    emptyForm()
    if (modalInstance) {
      modalInstance.hide()
    }

  }
  catch (e) {
    alertStore.showAlert(1, `${formData.value.tuotenimi} ${i18n.t('message.ei_lisatty')}: ${e}`)
  }

  emptyForm()
  closeOverlay()
}

</script>


<template>
  <div>
    <button v-if="store.isLoggedIn" type="button" class="btn btn-primary" data-bs-toggle="modal" data-bs-target="#addModal">
      {{ $t('message.uusi_laite') }}
    </button>
    <teleport to="body">
      <div class="modal fade" id="addModal" tabindex="-1" aria-labelledby="addModalLabel" aria-hidden="true">
        <div class="modal-dialog modal-dialog-centered modal-lg">
          <div class="modal-content">
            <div class="modal-header">
              <h5 class="modal-title" id="addModalLabel">{{ $t('message.tiedot_uusi') }}</h5>
              <button type="button" class="btn-close" data-bs-dismiss="modal" aria-label="Close"></button>
            </div>
            <div class="modal-body">
              <form @submit.prevent="saveData" :class="{'was-validated': formValidated}" class="container compact-form" novalidate>
                <div class="row row-cols-2">
                  <div class="col d-flex flex-column gap-2">
                    <div>
                      <label for="tuotenimi">{{ $t('message.tuotenimi') }} <span class="text-danger">*</span></label>
                      <input class="form-control" id="tuotenimi" v-model="formData.tuotenimi" required />
                    </div>
                    <div>
                      <label for="merkki_ja_malli">{{ $t('message.merkki') }} <span class="text-danger">*</span></label>
                      <input id="merkki_ja_malli" class="form-control" v-model="formData.merkki_ja_malli" required />
                    </div>
                    <div>
                      <label for="kampus">{{ $t('message.kampus') }} <span class="text-danger">*</span></label>
                      <input id="kampus" class="form-control" v-model="formData.kampus" required />
                    </div>
                    <div>
                      <label for="yksikko">{{ $t('message.yksikko') }}</label>
                      <input id="yksikko" class="form-control" v-model="formData.yksikko" />
                    </div>
                    <div>
                      <label for="vastuuhenkilo">{{ $t('message.vastuuhenkilo') }}</label>
                      <input id="vastuuhenkilo" class="form-control" v-model="formData.vastuuhenkilo" />
                    </div>
                    <div>
                      <label for="toimituspvm">{{ $t('message.pvm') }}</label>
                      <input id="toimituspvm" v-model="formData.toimituspvm" type="date" class="form-control" />
                    </div>
                    <div>
                      <label for="edellinen_huolto">{{ $t('message.edellinen_huolto') }}</label>
                      <input id="edellinen_huolto" class="form-control" v-model="formData.edellinen_huolto"
                        type="date" />
                    </div>
                  </div>
                  <div class="col d-flex flex-column gap-2">
                    <div>
                      <label for="sarjanumero">{{ $t('message.sarjanumero') }}</label>
                      <input id="sarjanumero" class="form-control" v-model="formData.sarjanumero" />
                    </div>
                    <div>
                      <label for="tay_numero">{{ $t('message.tay') }}</label>
                      <input id="tay_numero" class="form-control" v-model="formData.tay_numero" placeholder="12345" />
                    </div>
                    <div>
                      <label for="huone">{{ $t('message.huone') }}</label>
                      <input id="huone" class="form-control" v-model="formData.huone" placeholder="ARVO-D007" />
                    </div>
                    <div>
                      <label for="rakennus">{{ $t('message.rakennus') }}</label>
                      <input id="rakennus" class="form-control" v-model="formData.rakennus" />
                    </div>
                    <div>
                      <label for="toimittaja">{{ $t('message.toimittaja') }}</label>
                      <input id="toimittaja" class="form-control" v-model="formData.toimittaja" />
                    </div>
                    <div>
                      <label for="huoltosopimus_loppuu">{{ $t('message.huoltosopimus_loppuu') }}</label>
                      <input id="huoltosopimus_loppuu" class="form-control" v-model="formData.huoltosopimus_loppuu"
                        type="date" />
                    </div>
                    <div>
                      <label for="seuraava_huolto">{{ $t('message.seuraava_huolto') }}</label>
                      <input id="seuraava_huolto" class="form-control" v-model="formData.seuraava_huolto" type="date" />
                    </div>
                  </div>
                  <div class="mt-3">
                    <label for="lisatieto">{{ $t('message.lisatieto') }}</label>
                    <textarea id="lisatieto" type="text" class="form-control" v-model="formData.lisatieto" />
                  </div>
                </div>
              </form>
            </div>
            <div class="modal-footer">
              <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">{{ $t('message.peruuta')
                }}</button>
              <button type="button" class="btn btn-primary" @click="saveData">{{
                $t('message.tallenna') }}</button>
            </div>
          </div>
        </div>
      </div>
    </teleport>
  </div>
</template>

<style scoped>
label {
  margin-bottom: 0.2rem;
  font-size: 0.9rem;
}

/* Compact form styling */
.compact-form {
  gap: 0.5rem;
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

/* Only show invalid styling after form has been validated */
.compact-form.was-validated .form-control:invalid {
  border-color: #dc3545;
  background-image: none;
}

.compact-form.was-validated .form-control:invalid:focus {
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
