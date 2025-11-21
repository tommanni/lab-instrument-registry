<script setup>
import axios from 'axios'
import { ref, onMounted } from 'vue'
import { useDataStore } from '@/stores/data'
import { useAlertStore } from '@/stores/alert'
import { useI18n } from 'vue-i18n';
import { Modal } from 'bootstrap';
import { getFileIcon, formatFileSize } from '@/utils/fileUtils';

const { t } = useI18n();
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

    modalElement.addEventListener('show.bs.modal', () => {
      formValidated.value = false
    })

    modalElement.addEventListener('hidden.bs.modal', () => {
      formValidated.value = false
      emptyForm()
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

// Attachment handling
const pendingAttachments = ref([])
const fileInputRef = ref(null)

const handleFileSelect = (event) => {
  const files = Array.from(event.target.files)

  files.forEach(file => {
    // Validate file size (20MB)
    if (file.size > 20971520) {
      alertStore.showAlert(1, `${file.name}: ${t('message.tiedosto_liian_suuri')}`)
      if (fileInputRef.value) {
        fileInputRef.value.value = ''
      }
      return
    }
    pendingAttachments.value.push({
      file: file,
      description: '',
      tempId: Date.now() + Math.random()
    })
  })

  // Reset input so same file can be selected again
  if (fileInputRef.value) {
    fileInputRef.value.value = ''
  }
}

const removePendingAttachment = (tempId) => {
  pendingAttachments.value = pendingAttachments.value.filter(a => a.tempId !== tempId)
}


const closeOverlay = () => {
  showOverlay.value = false
}

const emptyForm = () => {
  formData.value = createFormDataWithMaintenance()
  pendingAttachments.value = []
  if (fileInputRef.value) {
    fileInputRef.value.value = ''
  }
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

  // Validate attachment descriptions before saving
  const missingDescriptions = pendingAttachments.value.filter(
    a => !a.description || !a.description.trim()
  )
  if (missingDescriptions.length > 0) {
    alertStore.addAlert(t('message.kuvaus_vaaditaan'), 'danger')
    return // Don't save if attachment validation fails
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

    alertStore.showAlert(0, `${dataToSend.tuotenimi} ${t('message.lisatty')}`)
    const savedItem = response.data
    store.addObject(savedItem)
    emit('new-instrument-added', savedItem)

    // Upload attachments if any
    if (pendingAttachments.value.length > 0) {
      const uploadErrors = []
      for (const attachment of pendingAttachments.value) {
        const formData = new FormData()
        formData.append('file', attachment.file)
        formData.append('description', attachment.description.trim())

        try {
          await axios.post(
            `/api/instruments/${savedItem.id}/attachments/`,
            formData,
            {
              withCredentials: true,
              headers: {
                'Content-Type': 'multipart/form-data'
              }
            }
          )
        } catch (error) {
          console.error('Error uploading attachment:', error)
          uploadErrors.push(`${attachment.file.name}: ${error.response?.data?.detail || 'Upload failed'}`)
        }
      }

      if (uploadErrors.length > 0) {
        alertStore.showAlert(1, `Some attachments failed to upload: ${uploadErrors.join(', ')}`)
      }
    }

    // Close modal only on successful save
    emptyForm()
    pendingAttachments.value = [] // Clear attachments
    if (modalInstance) {
      modalInstance.hide()
    }

  }
  catch (e) {
    alertStore.showAlert(1, `${formData.value.tuotenimi} ${t('message.ei_lisatty')}: ${e}`)
  }

  emptyForm()
  closeOverlay()
}

</script>


<template>
  <div>
    <button v-if="store.isLoggedIn" type="button" class="btn btn-primary add-button" data-bs-toggle="modal" data-bs-target="#addModal">
      <i class="bi bi-plus-lg add-button-icon" aria-hidden="true"></i>
      {{ t('message.uusi_laite') }}
    </button>
    <teleport to="body">
      <div class="modal fade" id="addModal" tabindex="-1" aria-labelledby="addModalLabel" aria-hidden="true">
        <div class="modal-dialog modal-dialog-centered modal-lg">
          <div class="modal-content">
            <div class="modal-header">
              <h5 class="modal-title" id="addModalLabel">{{ t('message.tiedot_uusi') }}</h5>
              <button type="button" class="btn-close" data-bs-dismiss="modal" aria-label="Close"></button>
            </div>
            <div class="modal-body">
              <form @submit.prevent="saveData" :class="{'was-validated': formValidated}" class="container compact-form" novalidate>
                <div class="row row-cols-2">
                  <div class="col d-flex flex-column" style="gap: 0.33rem;">
                    <div>
                      <label for="tuotenimi">{{ t('message.tuotenimi') }} <span class="text-danger">*</span></label>
                      <input class="form-control" id="tuotenimi" v-model="formData.tuotenimi" required />
                    </div>
                    <div>
                      <label for="merkki_ja_malli">{{ t('message.merkki') }} <span class="text-danger">*</span></label>
                      <input id="merkki_ja_malli" class="form-control" v-model="formData.merkki_ja_malli" required />
                    </div>
                    <div>
                      <label for="kampus">{{ t('message.kampus') }} <span class="text-danger">*</span></label>
                      <input id="kampus" class="form-control" v-model="formData.kampus" required />
                    </div>
                    <div>
                      <label for="yksikko">{{ t('message.yksikko') }}</label>
                      <input id="yksikko" class="form-control" v-model="formData.yksikko" />
                    </div>
                    <div>
                      <label for="vastuuhenkilo">{{ t('message.vastuuhenkilo') }}</label>
                      <input id="vastuuhenkilo" class="form-control" v-model="formData.vastuuhenkilo" />
                    </div>
                    <div>
                      <label for="toimituspvm">{{ t('message.pvm') }}</label>
                      <input id="toimituspvm" v-model="formData.toimituspvm" type="date" class="form-control" />
                    </div>
                    <div>
                      <label for="edellinen_huolto">{{ t('message.edellinen_huolto') }}</label>
                      <input id="edellinen_huolto" class="form-control" v-model="formData.edellinen_huolto"
                        type="date" />
                    </div>
                  </div>
                  <div class="col d-flex flex-column" style="gap: 0.33rem;">
                    <div>
                      <label for="sarjanumero">{{ t('message.sarjanumero') }}</label>
                      <input id="sarjanumero" class="form-control" v-model="formData.sarjanumero" />
                    </div>
                    <div>
                      <label for="tay_numero">{{ t('message.tay') }}</label>
                      <input id="tay_numero" class="form-control" v-model="formData.tay_numero" placeholder="12345" />
                    </div>
                    <div>
                      <label for="huone">{{ t('message.huone') }}</label>
                      <input id="huone" class="form-control" v-model="formData.huone" placeholder="ARVO-D007" />
                    </div>
                    <div>
                      <label for="rakennus">{{ t('message.rakennus') }}</label>
                      <input id="rakennus" class="form-control" v-model="formData.rakennus" />
                    </div>
                    <div>
                      <label for="toimittaja">{{ t('message.toimittaja') }}</label>
                      <input id="toimittaja" class="form-control" v-model="formData.toimittaja" />
                    </div>
                    <div>
                      <label for="huoltosopimus_loppuu">{{ t('message.huoltosopimus_loppuu') }}</label>
                      <input id="huoltosopimus_loppuu" class="form-control" v-model="formData.huoltosopimus_loppuu"
                        type="date" />
                    </div>
                    <div>
                      <label for="seuraava_huolto">{{ t('message.seuraava_huolto') }}</label>
                      <input id="seuraava_huolto" class="form-control" v-model="formData.seuraava_huolto" type="date" />
                    </div>
                  </div>
                  <div class="mt-3">
                    <label for="lisatieto">{{ t('message.lisatieto') }}</label>
                    <textarea id="lisatieto" type="text" class="form-control" v-model="formData.lisatieto" />
                  </div>
                </div>

                <!-- Attachments section -->
                <div class="mt-4 p-3 border rounded bg-light">
                  <h6 class="mb-3">{{ t('message.liitteet') }}</h6>

                  <div class="mb-3">
                    <input
                      ref="fileInputRef"
                      type="file"
                      class="form-control"
                      style="height: 31px; padding: 0.25rem 0.5rem; font-size: 0.875rem;"
                      @change="handleFileSelect"
                      multiple
                    />
                    <small class="text-muted">{{ t('message.max_tiedostokoko') }}: 20MB</small>
                  </div>

                  <!-- Pending attachments list -->
                  <div v-if="pendingAttachments.length > 0" class="attachments-list">
                    <div
                      v-for="attachment in pendingAttachments"
                      :key="attachment.tempId"
                      class="attachment-item p-2 mb-2 border rounded bg-white"
                    >
                      <div class="d-flex align-items-center justify-content-between mb-2">
                        <div class="flex-grow-1">
                          <div class="d-flex align-items-center">
                            <i :class="`bi ${getFileIcon(attachment.file.type)} me-2`"></i>
                            <div>
                              <div class="fw-bold small">{{ attachment.file.name }}</div>
                              <div class="text-muted" style="font-size: 0.75rem;">
                                {{ formatFileSize(attachment.file.size) }}
                              </div>
                            </div>
                          </div>
                        </div>
                        <button
                          @click="removePendingAttachment(attachment.tempId)"
                          class="icon-btn delete-icon"
                          type="button"
                          :title="t('message.poista')"
                        >
                          <i class="bi bi-trash"></i>
                        </button>
                      </div>
                      <div>
                        <input
                          v-model="attachment.description"
                          type="text"
                          class="form-control form-control-sm"
                          :class="{'is-invalid': formValidated && (!attachment.description || !attachment.description.trim())}"
                          :placeholder="t('message.kuvaus')"
                          required
                        />
                      </div>
                    </div>
                  </div>
                  <div v-else class="text-muted small">
                    {{ t('message.ei_liitteita') }}
                  </div>
                </div>
              </form>
            </div>
            <div class="modal-footer">
              <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">{{ t('message.peruuta')
                }}</button>
              <button type="button" class="btn btn-primary" @click="saveData">{{
                t('message.tallenna') }}</button>
            </div>
          </div>
        </div>
      </div>
    </teleport>
  </div>
</template>

<style scoped>
  .add-button-icon {
    padding-right: 4px;
  }
  .add-button {
    margin-top: 2px;
    margin-bottom: 4px;
    white-space: nowrap;
    height: 40px;
    display: inline-flex;
    align-items: center;
    justify-content: center;
    padding-left: 1rem;
    padding-right: 1rem;
    flex-shrink: 0;
  }

  @media screen and (max-width: 768px){
    .add-button {
      width: 100%;
      display: flex;
    }
  }

  /* Icon button styles matching AttachmentManager */
  .icon-btn {
    background: none;
    border: none;
    padding: 0.25rem;
    cursor: pointer;
    transition: all 0.15s ease;
    color: inherit;
  }

  .delete-icon {
    color: #dc3545;
  }

  .delete-icon:hover {
    font-weight: 900;
    transform: scale(1.1);
  }

  .delete-icon:disabled {
    opacity: 0.3;
    cursor: not-allowed;
  }
</style>
