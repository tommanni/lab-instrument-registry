<script setup>
import { ref, computed, watch} from 'vue';
import { useI18n } from 'vue-i18n';
import axios from 'axios';
import { useAlertStore } from "@/stores/alert.js";
import { defineProps, defineEmits } from 'vue';


const { t } = useI18n()
const alertStore = useAlertStore();

const props = defineProps({
  user: Object,
  actionType: String, // "admin" or "deactivate"
  show: Boolean
});

const emit = defineEmits(['update-user', 'close']);
const showOverlay = ref(props.show);

watch(() => props.show, (newVal) => {
    showOverlay.value = newVal;
});

const closeOverlay = () => {
    showOverlay.value = false;
    emit('close');
};

// Computed texts for template
const headerText = computed(() => 
  props.actionType === 'admin' 
    ? t('message.admin_oikeuksien_hallinta') 
    : t('message.deaktivoi_kayttaja')
);

// Function to handle confirmation action
const confirmAction = async () => {
    try {
        if (props.actionType === 'admin') {
            const res = await axios.post('/api/change-admin-status/',
                { id: props.user.id }, { withCredentials: true });
            emit('update-user', { ...props.user, is_superuser: res.data.newAdminStatus });
            
            alertStore.showAlert(0, res.data.newAdminStatus
            ? t('message.admin_luotu')
            : t('message.admin_poistettu'));
    
        } else if (props.actionType === 'deactivate') {
            const res = await axios.post('/api/change-active-status/',
                { id: props.user.id },
                { withCredentials: true });
            emit('update-user', { ...props.user, is_active: res.data.newActiveStatus });

            alertStore.showAlert(0, res.data.newActiveStatus
                ? t('message.kayttaja_aktivoitu')
                : t('message.kayttaja_deaktivoitu')
            );
        }
    } catch (error) {
        alertStore.showAlert(1, t('message.virhe'));
    } finally {
        closeOverlay();
    }
};
</script>

<template>
  <div v-if="showOverlay" class="overlay-backdrop">
    <div class="overlay-content">
      <button type="button"
            class="btn-close position-absolute top-0 end-0 m-3"
            @click="closeOverlay"
            aria-label="Close"></button>

      <!-- Show different content for overlay depending on action type (admin/deactivate) -->
      <h3>{{ actionType === 'admin'
            ? t('message.admin_oikeuksien_hallinta')
            : t('message.kayttajan_hallinta') }}</h3>
      <p>
        {{ actionType === 'admin'
          ? (props.user.is_superuser
          ? t('message.haluatko_poistaa_adminin')
          : t('message.haluatko_tehda_adminin')
            )
          : (props.user.is_active
          ? t('message.haluatko_deaktivoida_kayttajan')
          : t('message.aktivoi_kayttaja')) }}
      </p>

      <div class="modal-buttons">
        <button class="btn btn-secondary me-2" @click="closeOverlay">{{  t('message.peruuta') }}</button>
        <button class="btn btn-danger" @click="confirmAction">{{ t('message.vahvista_muutokset') }}</button>
      </div>
    </div>
  </div>
</template>


<style scoped>

.admin-container {
  max-width: 600px;
  width: 100%;
  margin: 20px auto;
  padding: 1rem;
  box-sizing: border-box;
}

.overlay-backdrop {
  position: fixed;
  top: 0; left: 0; right: 0; bottom: 0;
  background-color: rgba(0,0,0,0.5);
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
  box-shadow: 0 2px 10px rgba(0,0,0,0.3);
  max-width: 500px;
  width: 100%;
  box-sizing: border-box;
}

.modal-buttons button {
  margin-top: 1rem;
}



</style>