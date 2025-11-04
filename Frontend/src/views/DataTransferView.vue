<script setup>
import { useI18n } from 'vue-i18n';
import axios from 'axios';
import { ref } from 'vue';
import { useAlertStore } from '@/stores/alert';
import ImportPreviewModal from '@/components/ImportPreviewModal.vue';

const { t } = useI18n();
const alertStore = useAlertStore();
const isImporting = ref(false);
const isExporting = ref(false);
const selectedFile = ref(null);
const previewData = ref(null);
const previewModalRef = ref(null);
const fileInputRef = ref(null);

// Import
const onFileSelected = (event) => {
  selectedFile.value = event.target.files[0];
};

const previewImport = async () => {
  if (!selectedFile.value) {
    alertStore.showAlert(1, t('message.valitse_tiedosto_ensin'));
    return;
  }

  const formData = new FormData();
  formData.append('file', selectedFile.value);

  try {
    const response = await axios.post('/api/instruments/csv/preview/', formData, {
      withCredentials: true
    });

    previewData.value = response.data;
    previewModalRef.value?.show();
  } catch (error) {
    console.error('Preview failed:', error);
    alertStore.showAlert(1, error.response?.data?.error || t('message.tiedoston_lukeminen_epaonnistui'));
  }
};

const confirmImport = async () => {
  if (!selectedFile.value) return;

  isImporting.value = true;
  const formData = new FormData();
  formData.append('file', selectedFile.value);

  try {
    const response = await axios.post('/api/instruments/csv/import/', formData, {
      withCredentials: true
    });

    previewModalRef.value?.hide();
    resetImport();
    alertStore.showAlert(0, t('message.tiedot_tuotu_onnistuneesti', { count: response.data.imported_count }));
  } catch (error) {
    console.error('Import failed:', error);
    alertStore.showAlert(1, error.response?.data?.error || t('message.tiedoston_tuonti_epaonnistui'));
  } finally {
    isImporting.value = false;
  }
};

const resetImport = () => {
  selectedFile.value = null;
  previewData.value = null;
  // Clear the file input element
  if (fileInputRef.value) {
    fileInputRef.value.value = '';
  }
};

const cancelImport = () => {
  resetImport();
};

// Helper function to download file
const downloadFile = async (url, filename) => {
  try {
    const response = await axios.get(url, {
      responseType: 'blob',
      withCredentials: true
    });

    const blobUrl = window.URL.createObjectURL(new Blob([response.data]));
    const link = document.createElement('a');
    link.href = blobUrl;
    link.setAttribute('download', filename);
    document.body.appendChild(link);
    link.click();
    link.remove();
    window.URL.revokeObjectURL(blobUrl);
  } catch (error) {
    throw error;
  }
};

// Export
const exportData = async () => {
  isExporting.value = true;
  try {
    const filename = 'laiterekisteri_' + new Date().toISOString().split('T')[0] + '.csv';
    await downloadFile('/api/instruments/csv/export/', filename);
  } catch (error) {
    console.error('Export failed:', error);
    alertStore.showAlert(1, t('message.tiedot_vienti_epaonnistui'));
  } finally {
    isExporting.value = false;
  }
};

</script>

<template>
  <div class="content">
    <h3 class="mb-4">{{ t('message.tiedonsiirto') }}</h3>
    <div class="row g-4">
      <!-- Import Card -->
      <div class="col-md-6">
        <div class="card h-100">
          <div class="card-body">
            <h4 class="card-title mb-3">{{ t('message.tuo_tiedot_nappi') }}</h4>
            <p class="card-text mb-4">
              {{ t('message.tuo_tiedot_kuvaus') }}
            </p>
            <div class="d-grid gap-2">
              <div class="input-group">
                <input
                  ref="fileInputRef"
                  type="file"
                  class="form-control"
                  accept=".csv"
                  @change="onFileSelected"
                  :disabled="isImporting"
                />
              </div>
              <!-- TODO: Re-enable with :disabled="!selectedFile || isImporting" -->
              <button
                class="btn btn-primary"
                @click="previewImport"
                :disabled="true"
              >
                <span v-if="isImporting">
                  <span class="spinner-border spinner-border-sm me-2" role="status" aria-hidden="true"></span>
                  {{ t('message.tuodaan') }}...
                </span>
                <span v-else>
                  {{ t('message.tuo_tiedot_nappi') }}
                </span>
              </button>
            </div>
          </div>
        </div>
      </div>

      <!-- Export Card -->
      <div class="col-md-6">
        <div class="card h-100">
          <div class="card-body">
            <h4 class="card-title mb-3">{{ t('message.vie_instrumenttirekisteri') }}</h4>
            <p class="card-text mb-4">
              {{ t('message.vie_tiedot_kuvaus') }}
            </p>
            <div class="d-grid gap-2">
              <button
                class="btn btn-primary"
                @click="exportData"
                :disabled="isExporting"
              >
                <span v-if="isExporting">
                  <span class="spinner-border spinner-border-sm me-2" role="status" aria-hidden="true"></span>
                  {{ t('message.viedaan') }}...
                </span>
                <span v-else>
                  {{ t('message.vie_instrumenttirekisteri') }}
                </span>
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Import Preview Modal -->
    <ImportPreviewModal
      ref="previewModalRef"
      :preview-data="previewData"
      :is-importing="isImporting"
      @confirm="confirmImport"
      @cancel="cancelImport"
    />
  </div>
</template>

<style scoped>
.content {
  padding-bottom: 88px;
}

.card {
  border: 1px solid #dee2e6;
  border-radius: 8px;
  box-shadow: 0 2px 4px rgba(0,0,0,0.1);
  transition: box-shadow 0.3s ease;
}

.card:hover {
  box-shadow: 0 4px 8px rgba(0,0,0,0.15);
}

.card-title {
  color: #4E008E;
  font-weight: 600;
}
</style>

