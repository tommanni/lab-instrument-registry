<script setup>
import { ref, computed } from 'vue'
import { useI18n } from 'vue-i18n'
import axios from 'axios'
import { useAlertStore } from "@/stores/alert.js";

const { t } = useI18n()

const showOverlay = ref(false);
const alertStore = useAlertStore();
const new_password = ref('');
const confirm_new_password = ref('');
const props = defineProps({
    user: Object,
    warningVisible: Boolean
});

const extraMargin = computed(() => props.warningVisible ? '3rem' : '1rem');

const openOverlay = () => {
    showOverlay.value = true
}

const closeOverlay = () => {
    showOverlay.value = false;
    new_password.value = '';
    confirm_new_password.value = '';

}

async function submitPassword() {
    if (!new_password.value || !confirm_new_password.value) {
        alertStore.showAlert(1, t('message.tayta_molemmat_kentat'));
        return;
    }
    if (new_password.value !== confirm_new_password.value) {
        alertStore.showAlert(1, t('message.salasanat_eivat_tasmaa'));
        return;
    }

    try {
       await axios.post(
            '/api/change-password/',
            {
            new_password: new_password.value,
            id: props.user.id
            },
            {
            withCredentials: true
        });

        alertStore.showAlert(0, t('message.salasana_vaihdettu'));
        new_password.value = '';
        confirm_new_password.value = '';
        closeOverlay()
    } catch (error) {
        if (error.response && error.response.data && error.response.data.message) {
            alertStore.showAlert(1, t('message.virhe') + error.response.data.message);
        }
        else {
            alertStore.showAlert(1, t('message.tuntematon_virhe'));
        }

    }
}




</script>



<template>
    <div class="change-password-btn">
        <!-- Change password button to open overlay -->
        <button class="btn btn-primary" @click="openOverlay">
            {{ t('message.vaihda_salasana') }}
        </button>
    </div>

    <!-- Overlay -->
    <div v-if="showOverlay" class="overlay-backdrop">
        <div class="overlay-content" >
          <!-- Close button in top right corner -->
        <button type="button"
            class="btn-close position-absolute top-0 end-0 m-3"
                @click="closeOverlay" aria-label="Close"></button>
            
            <h3>{{ t('message.vaihda_salasana') }}</h3>
            <div class="password-field">
            <label class="form-label">{{ t('message.uusi_salasana') }}</label>
            <input
                v-model="new_password"
                type="password"
                :placeholder="t('message.uusi_salasana')"
                />

                <div class="password-field">
                <label class="form-label">{{ t('message.vahvista_salasana') }}</label>
                <input
                    v-model="confirm_new_password"
                    type="password"
                    :placeholder="t('message.vahvista_salasana')"
                />

                <div class="modal-buttons">
                <button class="btn btn-primary" @click="submitPassword">
                    {{ t('message.vahvista_muutokset') }}
                </button>
                </div>
                </div>
            </div>
        </div>    
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
  padding: 3em 3.5em;
  border-radius: 4px;
  box-shadow: 0 2px 10px rgba(0, 0, 0, 0.3);
  max-width: 600px;
  width:90%;
}

.overlay-content h3 {
  margin-bottom: 1.5rem;
}

.password-field label {
  display:block;
  margin-bottom: 0.5rem;
  font-weight: 500;
}

.password-field input {
  display: block;
  width: 100%;
  max-width: 400px;
  padding: 0.5rem 0.75rem;
  border: 1px solid #ccc;
  border-radius: 4px;
  box-sizing: border-box;
  margin-bottom: 1rem;
}

.modal-buttons button {
  margin-top: 1rem;
}

</style>