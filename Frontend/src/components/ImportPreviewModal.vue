<template>
  <div class="modal fade" id="importPreviewModal" tabindex="-1" aria-labelledby="importPreviewModalLabel" aria-hidden="true">
    <div class="modal-dialog modal-lg">
      <div class="modal-content">
        <div class="modal-header">
          <h5 class="modal-title" id="importPreviewModalLabel">{{ t('message.tarkista_tuonti') }}</h5>
          <button type="button" class="btn-close" @click="handleCancel" :disabled="isImporting" aria-label="Close"></button>
        </div>
        <div class="modal-body">
          <div v-if="previewData">
            <!-- Summary -->
            <div class="alert alert-info">
              <h6 class="mb-3">{{ t('message.tuontisummary') }}</h6>
              <ul class="mb-0">
                <li>{{ t('message.yhteensa_rivit') }}: {{ previewData.total_rows }}</li>
                <li>{{ t('message.uudet_laitteet') }}: {{ previewData.new_count }}</li>
                <li>{{ t('message.duplikaatit') }}: {{ previewData.duplicate_count }}</li>
                <li v-if="previewData.invalid_count > 0">{{ t('message.virheelliset_rivit') }}: {{ previewData.invalid_count }}</li>
              </ul>
            </div>

            <!-- Invalid Rows Warning -->
            <div v-if="previewData.invalid_count > 0" class="mb-3">
              <h6 class="text-danger">{{ t('message.varoitus_virheelliset') }}</h6>
              <p class="small text-muted mb-2">{{ t('message.virheelliset_kuvaus') }}</p>
              <div class="table-responsive" style="max-height: 250px; overflow-y: auto;">
                <table class="table table-sm mb-0">
                  <thead class="table-light">
                    <tr>
                      <th class="small">TAY-numero</th>
                      <th class="small">Tuotenimi</th>
                      <th class="small">Merkki ja malli</th>
                    </tr>
                  </thead>
                  <tbody>
                    <tr v-for="(invalid, idx) in previewData.invalid_rows" :key="idx" class="small">
                      <td>{{ invalid.tay_numero }}</td>
                      <td>{{ invalid.tuotenimi }}</td>
                      <td>{{ invalid.merkki_ja_malli }}</td>
                    </tr>
                  </tbody>
                </table>
              </div>
              <small v-if="previewData.has_more_invalid" class="text-muted d-block mt-2">
                {{ t('message.ja_lisaa_virheellisia') }}
              </small>
            </div>

            <!-- Duplicates Warning -->
            <div v-if="previewData.duplicate_count > 0" class="mb-3">
              <h6 class="text-warning">{{ t('message.varoitus_duplikaatit') }}</h6>
              <p class="small text-muted mb-2">{{ t('message.duplikaatit_kuvaus_valitse') }}</p>
              <div class="table-responsive" style="max-height: 250px; overflow-y: auto;">
                <table class="table table-sm mb-0">
                  <thead class="table-light">
                    <tr>
                      <th class="small" style="width: 5%;">
                        <input
                          class="form-check-input"
                          type="checkbox"
                          :checked="areAllDuplicatesSelected"
                          @change="toggleSelectAllDuplicates"
                        />
                      </th>
                      <th class="small">TAY-numero</th>
                      <th class="small">Tuotenimi</th>
                      <th class="small">Merkki ja malli</th>
                    </tr>
                  </thead>
                  <tbody>
                    <tr v-for="(dup, idx) in previewData.duplicates" :key="idx" class="small">
                      <td>
                        <input
                          class="form-check-input"
                          type="checkbox"
                          :checked="selectedDuplicates.has(idx)"
                          @change="() => toggleDuplicateSelection(idx)"
                        />
                      </td>
                      <td>{{ dup.tay_numero }}</td>
                      <td>{{ dup.tuotenimi }}</td>
                      <td>{{ dup.merkki_ja_malli }}</td>
                    </tr>
                  </tbody>
                </table>
              </div>
            </div>

            <!-- No new instruments warning -->
            <div v-if="previewData.new_count === 0 && previewData.duplicate_count > 0" class="alert alert-warning mb-0">
              <strong class="small">{{ t('message.ei_uusia_laitteita_duplikaatteja') }}</strong>
              <p class="small mb-0 mt-1">{{ t('message.ei_uusia_laitteita_duplikaatteja_kuvaus') }}</p>
            </div>
            <div v-else-if="previewData.new_count === 0" class="alert alert-warning mb-0">
              <strong class="small">{{ t('message.ei_uusia_laitteita') }}</strong>
              <p class="small mb-0 mt-1">{{ t('message.ei_uusia_laitteita_kuvaus') }}</p>
            </div>

            <!-- Import Warning -->
            <div v-else class="alert alert-danger mb-0">
              <strong class="small">{{ t('message.varoitus_tuonti') }}</strong>
              <p class="small mb-0 mt-1">{{ t('message.varoitus_tuonti_kuvaus') }}</p>
            </div>
          </div>
        </div>
        <div class="modal-footer">
          <button type="button" class="btn btn-secondary" @click="handleCancel" :disabled="isImporting">
            {{ t('message.peruuta') }}
          </button>
          <button
            type="button"
            class="btn btn-danger"
            @click="handleConfirm"
            :disabled="isImporting || !previewData || (previewData.new_count === 0 && selectedDuplicates.size === 0)"
          >
            <span v-if="isImporting" class="spinner-border spinner-border-sm me-2" role="status" aria-hidden="true"></span>
            {{ isImporting ? t('message.tuodaan') + '...' : t('message.vahvista_tuonti') }}
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, computed, watch } from 'vue';
import { useI18n } from 'vue-i18n';
import { Modal } from 'bootstrap';

const { t } = useI18n();

const props = defineProps({
  previewData: {
    type: Object,
    default: null
  },
  isImporting: {
    type: Boolean,
    default: false
  }
});

const emit = defineEmits(['confirm', 'cancel']);

const modalInstance = ref(null);
const selectedDuplicates = ref(new Set());

// Reset selections when previewData changes
watch(() => props.previewData, () => {
  selectedDuplicates.value.clear();
});

const areAllDuplicatesSelected = computed(() => {
  if (!props.previewData || !props.previewData.duplicates || props.previewData.duplicates.length === 0) {
    return false;
  }
  return selectedDuplicates.value.size === props.previewData.duplicates.length;
});

const toggleDuplicateSelection = (index) => {
  if (selectedDuplicates.value.has(index)) {
    selectedDuplicates.value.delete(index);
  } else {
    selectedDuplicates.value.add(index);
  }
};

const toggleSelectAllDuplicates = () => {
  if (areAllDuplicatesSelected.value) {
    selectedDuplicates.value.clear();
  } else {
    if (props.previewData && props.previewData.duplicates) {
      props.previewData.duplicates.forEach((_, index) => {
        selectedDuplicates.value.add(index);
      });
    }
  }
};

onMounted(() => {
  const modalElement = document.getElementById('importPreviewModal');
  if (modalElement) {
    modalInstance.value = new Modal(modalElement, {
      backdrop: 'static',
      keyboard: true
    });

    // Listen for modal hidden event to emit cancel (handles ESC key)
    modalElement.addEventListener('hidden.bs.modal', () => {
      emit('cancel');
    });
  }
});

const show = () => {
  modalInstance.value?.show();
};

const hide = () => {
  modalInstance.value?.hide();
};

const handleCancel = () => {
  hide();
  // Cancel event will be emitted by the hidden.bs.modal listener
};

const handleConfirm = () => {
  const duplicatesToImport = props.previewData.duplicates.filter((_, index) => selectedDuplicates.value.has(index));
  emit('confirm', { duplicatesToImport });
};

// Expose methods to parent
defineExpose({
  show,
  hide
});
</script>
