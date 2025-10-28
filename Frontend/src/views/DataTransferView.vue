<script setup>
import { useI18n } from 'vue-i18n';
import axios from 'axios';
import { ref } from 'vue';
import { useAlertStore } from '@/stores/alert';

const { t } = useI18n();
const alertStore = useAlertStore();
const isExporting = ref(false);

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
    await downloadFile('/api/instruments/csv/', filename);
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
    <h3 class="mb-4">{{ t('message.vie_tiedot') }}</h3>
    <div class="row justify-content-center">
      <!-- Export Card -->
      <div class="col-md-8 col-lg-6">
        <div class="card">
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

