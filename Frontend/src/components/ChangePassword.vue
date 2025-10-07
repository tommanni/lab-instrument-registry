<script setup>
import axios from 'axios';
import { ref, computed } from 'vue';
import { useAlertStore } from '@/stores/alert';
import { useI18n } from 'vue-i18n';

const { t, tm } = useI18n();
const alertStore = useAlertStore();
const new_password = ref('');
const confirm_new_password = ref('');
const props = defineProps({
    user: Object,
    warningVisible: Boolean });

const extraMargin = computed(() => props.warningVisible ? '3rem' : '1rem');


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
        id : props.user.id
      },
      { 
      withCredentials: true
    });
    alertStore.showAlert(0, t('message.salasana_vaihdettu'));
  } catch (error) {
    alertStore.showAlert(1, t('message.virhe'));
  }
  new_password.value = '';
  confirm_new_password.value = '';
}

</script>

<template>
  <div class="password-container" :style="{ marginTop: extraMargin }">
    <h3>{{ t('message.vaihda_salasana') }}</h3>

    <div class="password-field">
      <label class="form-label">{{ t('message.uusi_salasana') }}</label>
      <input
        v-model="new_password"
        type="password"
        :placeholder="t('message.uusi_salasana')"
      />
    </div>
    
    <div class="password-field">
      <label class="form-label">{{ t('message.vahvista_salasana') }}</label>
      <input
        v-model="confirm_new_password"
        type="password"
        :placeholder="t('message.vahvista_salasana')"
      />
    </div>

    <div class="modal-buttons">
      <button @click="submitPassword">{{ t('message.vahvista_muutokset') }}</button>
    </div>
  </div>
</template>

<style scoped>
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
}

.password-container {
  transition: margin-top 0.3s ease;
}

.modal-buttons button {
  margin-top: 1rem;
  border-radius: 4px;
  border: none;
  padding: 5px 10px;
  color: white;
  background-color: #cf286f;

}

</style>