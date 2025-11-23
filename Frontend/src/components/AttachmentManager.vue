<script setup>
import { ref, watch, computed, onMounted } from 'vue';
import { useI18n } from 'vue-i18n';
import { useAlertStore } from '@/stores/alert';
import { useDataStore } from '@/stores/data';
import { getFileIcon, formatFileSize } from '@/utils/fileUtils';
import axios from 'axios';

const { t } = useI18n();
const alertStore = useAlertStore();
const dataStore = useDataStore();

const props = defineProps({
  instrumentId: {
    type: Number,
    required: true
  },
  isEditMode: {
    type: Boolean,
    default: false
  }
});

const attachments = ref([]);
const isLoading = ref(false);
const isUploading = ref(false);
const selectedFile = ref(null);
const fileDescription = ref('');
const fileInputRef = ref(null);
const deleteConfirmId = ref(null);
const showDeleteConfirm = ref(false);
const pendingUploads = ref([]); // Files waiting to be uploaded when Päivitä is clicked
const pendingDeletes = ref([]); // Attachment IDs to delete when Päivitä is clicked

const fetchAttachments = async (retryCount = 0) => {
  if (!props.instrumentId) return;

  isLoading.value = true;
  try {
    const response = await axios.get(
      `/api/instruments/${props.instrumentId}/attachments/`,
      { withCredentials: true }
    );
    attachments.value = response.data;
  } catch (error) {
    // 401 errors are expected when not logged in - don't clear attachments
    if (error.response?.status === 401) {
      // User not authenticated - this is expected
    } else if (error.response?.status === 500 && retryCount < 3) {
      // Retry on server errors (up to 3 times)
      console.warn(`Server error fetching attachments, retrying (attempt ${retryCount + 1}/3)...`);
      isLoading.value = false;
      await new Promise(resolve => setTimeout(resolve, 500)); // Wait 500ms before retry
      return fetchAttachments(retryCount + 1);
    } else {
      console.error('Error fetching attachments:', error);
      // For other errors, clear attachments
      attachments.value = [];
    }
  } finally {
    isLoading.value = false;
  }
};

// Fetch attachments on component mount
onMounted(() => {
  if (props.instrumentId && dataStore.isLoggedIn) {
    fetchAttachments();
  }
});

// Fetch attachments when instrument ID changes
watch(() => props.instrumentId, async (newId) => {
  if (newId) {
    try {
      await fetchAttachments();
    } catch (error) {
      console.error('Error in watch fetchAttachments:', error);
    }
  }
}, { immediate: true });

// Refetch attachments when login state changes
watch(() => dataStore.isLoggedIn, async (isLoggedIn) => {
  if (isLoggedIn && props.instrumentId) {
    try {
      await fetchAttachments();
    } catch (error) {
      console.error('Error refetching attachments after login:', error);
    }
  }
});

const handleFileSelect = (event) => {
  const file = event.target.files[0];
  if (!file) {
    selectedFile.value = null;
    return;
  }

  // Validate file size (20MB)
  if (file.size > 20971520) {
    alertStore.showAlert(1, t('message.tiedosto_liian_suuri'));
    selectedFile.value = null;
    if (fileInputRef.value) {
      fileInputRef.value.value = '';
    }
    return;
  }

  selectedFile.value = file;
};

const uploadFile = () => {
  if (!selectedFile.value) {
    alertStore.showAlert(1, t('message.valitse_tiedosto_ensin'));
    return;
  }

  if (!fileDescription.value || fileDescription.value.trim() === '') {
    alertStore.showAlert(1, t('message.kuvaus_vaaditaan'));
    return;
  }

  // Add to pending uploads - will be uploaded when Päivitä is clicked
  pendingUploads.value.push({
    file: selectedFile.value,
    description: fileDescription.value.trim(),
    tempId: Date.now() + Math.random() // Temporary ID for UI
  });

  // Reset form
  selectedFile.value = null;
  fileDescription.value = '';
  if (fileInputRef.value) {
    fileInputRef.value.value = '';
  }
};

const confirmDelete = (attachmentId) => {
  deleteConfirmId.value = attachmentId;
  showDeleteConfirm.value = true;
};

const deleteAttachment = () => {
  const attachmentId = deleteConfirmId.value;
  showDeleteConfirm.value = false;

  // Add to pending deletes - will be deleted when Päivitä is clicked
  pendingDeletes.value.push(attachmentId);
};

const deletePendingUpload = (tempId) => {
  pendingUploads.value = pendingUploads.value.filter(u => u.tempId !== tempId);
};

// Process all pending changes when Päivitä is clicked
const isProcessing = ref(false);
const processPendingChanges = async () => {
  // Prevent double execution
  if (isProcessing.value) {
    return;
  }

  isProcessing.value = true;

  // Save to local variables to prevent them from being cleared during processing
  const deletesToProcess = [...pendingDeletes.value];
  const uploadsToProcess = [...pendingUploads.value];

  const errors = [];

  // Delete marked attachments first
  for (const attachmentId of deletesToProcess) {
    try {
      await axios.delete(
        `/api/attachments/${attachmentId}/`,
        { withCredentials: true }
      );
    } catch (error) {
      console.error('Error deleting attachment:', error);
      errors.push(`Delete failed for attachment ${attachmentId}`);
    }
  }

  // Then upload pending files
  for (const upload of uploadsToProcess) {
    // Validate description is not empty
    if (!upload.description || !upload.description.trim()) {
      errors.push(`${upload.file.name}: ${t('message.kuvaus_vaaditaan')}`);
      continue;
    }

    const formData = new FormData();
    formData.append('file', upload.file);
    formData.append('description', upload.description.trim());

    try {
      await axios.post(
        `/api/instruments/${props.instrumentId}/attachments/`,
        formData,
        {
          withCredentials: true,
          headers: {
            'Content-Type': 'multipart/form-data'
          }
        }
      );
    } catch (error) {
      console.error('Error uploading file:', error);
      // Check for disk space error (507 Insufficient Storage)
      if (error.response?.status === 507) {
        errors.push(t('message.palvelimen_tila_taynna'));
      } else {
        errors.push(`${upload.file.name}: ${error.response?.data?.detail || 'Upload failed'}`);
      }
    }
  }

  // Clear pending changes
  pendingUploads.value = [];
  pendingDeletes.value = [];

  // Refetch to show current state
  await fetchAttachments();

  // Show errors if any
  if (errors.length > 0) {
    alertStore.showAlert(1, `Some operations failed: ${errors.join(', ')}`);
  }

  // Reset processing flag
  isProcessing.value = false;
};

// Discard all pending changes when Peruuta is clicked
const discardPendingChanges = () => {
  pendingUploads.value = [];
  pendingDeletes.value = [];
};

const formatDate = (dateString) => {
  const date = new Date(dateString);
  return date.toLocaleDateString('fi-FI', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit'
  });
};

const hasPendingChanges = computed(() => {
  return pendingUploads.value.length > 0 || pendingDeletes.value.length > 0;
});

// Expose functions and state for parent component
defineExpose({
  processPendingChanges,
  discardPendingChanges,
  hasPendingChanges,
  pendingUploads,
  pendingDeletes
});
</script>

<template>
  <div v-if="dataStore.isLoggedIn" class="attachment-manager">
    <h6 class="mb-3">{{ t('message.liitteet') }}</h6>

    <!-- Upload form - only visible in edit mode -->
    <div v-if="isEditMode" class="upload-section mb-3 p-3 border rounded bg-light">
      <h6 class="mb-2">{{ t('message.lisaa_liite') }}</h6>
      <div class="mb-2">
        <input
          ref="fileInputRef"
          type="file"
          class="form-control"
          style="height: 31px; padding: 0.25rem 0.5rem; font-size: 0.875rem;"
          @change="handleFileSelect"
          :disabled="isUploading"
        />
        <small class="text-muted">{{ t('message.max_tiedostokoko') }}: 20MB</small>
      </div>
      <div class="mb-2">
        <input
          v-model="fileDescription"
          type="text"
          class="form-control form-control-sm"
          :placeholder="t('message.kuvaus')"
          :disabled="isUploading"
        />
      </div>
      <button
        @click="uploadFile"
        class="btn btn-sm"
        style="background-color: #4E008E; color: white;"
        :disabled="!selectedFile || isUploading"
      >
        <span v-if="isUploading" class="spinner-border spinner-border-sm me-1"></span>
        {{ isUploading ? t('message.ladataan') : t('message.lataa_tiedosto') }}
      </button>
    </div>

    <!-- Attachments list -->
    <div v-if="isLoading" class="text-center py-3">
      <div class="spinner-border spinner-border-sm" role="status">
        <span class="visually-hidden">{{ t('message.ladataan') }}...</span>
      </div>
    </div>

    <div v-else-if="attachments.length === 0 && pendingUploads.length === 0" class="text-muted small">
      {{ t('message.ei_liitteita') }}
    </div>

    <div v-else class="attachments-list">
      <!-- Existing attachments -->
      <div
        v-for="attachment in attachments"
        :key="attachment.id"
        class="attachment-item d-flex align-items-center justify-content-between mb-2 border rounded"
        :class="{ 'opacity-50 text-decoration-line-through': pendingDeletes.includes(attachment.id) }"
        style="padding: 0.5rem 0.75rem 0.5rem 0.5rem;"
      >
        <div class="flex-grow-1">
          <div class="d-flex align-items-center">
            <i :class="`bi ${getFileIcon(attachment.file_type)} me-2`"></i>
            <div>
              <a
                :href="attachment.file_url"
                target="_blank"
                class="text-decoration-none fw-bold"
                :class="{ 'text-muted': pendingDeletes.includes(attachment.id) }"
              >
                {{ attachment.filename }}
              </a>
              <div class="small text-muted">
                {{ formatFileSize(attachment.file_size) }}
                •
                {{ formatDate(attachment.uploaded_at) }}
                <span v-if="attachment.uploaded_by_name">
                  • {{ attachment.uploaded_by_name }}
                </span>
                <span v-if="pendingDeletes.includes(attachment.id)" class="badge bg-danger ms-2">
                  {{ t('message.poistetaan') }}
                </span>
              </div>
              <div v-if="attachment.description" class="small text-muted">
                {{ attachment.description }}
              </div>
            </div>
          </div>
        </div>
        <div class="d-flex gap-3 align-items-center">
          <a
            :href="`/api/attachments/${attachment.id}/download/`"
            class="icon-btn download-icon"
            :title="t('message.lataa')"
            :class="{ 'disabled': pendingDeletes.includes(attachment.id) }"
          >
            <i class="bi bi-download"></i>
          </a>
          <button
            v-if="isEditMode"
            @click="confirmDelete(attachment.id)"
            class="icon-btn delete-icon"
            :title="t('message.poista')"
            :disabled="pendingDeletes.includes(attachment.id)"
          >
            <i class="bi bi-trash"></i>
          </button>
        </div>
      </div>

      <!-- Pending uploads -->
      <div
        v-for="upload in pendingUploads"
        :key="upload.tempId"
        class="attachment-item d-flex align-items-center justify-content-between mb-2 border rounded border-success bg-light"
        style="padding: 0.5rem 0.75rem 0.5rem 0.5rem;"
      >
        <div class="flex-grow-1">
          <div class="d-flex align-items-center">
            <i :class="`bi ${getFileIcon(upload.file.type)} me-2`"></i>
            <div>
              <div class="fw-bold">
                {{ upload.file.name }}
              </div>
              <div class="small text-muted">
                {{ formatFileSize(upload.file.size) }}
                • <span class="badge bg-success">{{ t('message.odottaa_paivitysta') }}</span>
              </div>
              <div v-if="upload.description" class="small text-primary">
                {{ upload.description }}
              </div>
            </div>
          </div>
        </div>
        <div>
          <button
            @click="deletePendingUpload(upload.tempId)"
            class="icon-btn delete-icon"
            :title="t('message.poista')"
          >
            <i class="bi bi-trash"></i>
          </button>
        </div>
      </div>
    </div>

    <!-- Delete Confirmation Modal -->
    <div v-if="showDeleteConfirm" class="modal d-block" style="background-color: rgba(0, 0, 0, 0.5);">
      <div class="modal-dialog modal-dialog-centered">
        <div class="modal-content">
          <div class="modal-header">
            <h5 class="modal-title">{{ t('message.vahvista_liitteen_poisto') }}</h5>
            <button
              type="button"
              class="btn-close"
              @click="showDeleteConfirm = false"
            ></button>
          </div>
          <div class="modal-footer">
            <button
              type="button"
              class="btn btn-secondary"
              @click="showDeleteConfirm = false"
            >
              {{ t('message.peruuta') }}
            </button>
            <button
              type="button"
              class="btn btn-danger"
              @click="deleteAttachment"
            >
              {{ t('message.poista') }}
            </button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.attachment-manager {
  margin-top: 1rem;
}

.upload-section {
  background-color: #f8f9fa;
}

.attachment-item {
  transition: background-color 0.2s;
}

.attachment-item:hover {
  background-color: #f8f9fa;
}

.attachment-item a {
  color: var(--bs-primary);
}

.attachment-item a:hover {
  color: var(--bs-primary-hover-color, #6a1bb3);
  text-decoration: underline !important;
}

.icon-btn {
  background: none;
  border: none;
  padding: 0;
  cursor: pointer;
  font-size: 1.25rem;
  font-weight: 700;
  transition: all 0.2s;
  text-decoration: none;
}

.download-icon {
  color: var(--bs-primary);
}

.download-icon:hover {
  font-weight: 900;
  transform: scale(1.1);
}

.download-icon.disabled {
  opacity: 0.3;
  pointer-events: none;
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

