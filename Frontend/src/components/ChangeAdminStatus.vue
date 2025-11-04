<script setup>
import axios from 'axios';
import { useAlertStore } from '@/stores/alert';
import { useI18n } from 'vue-i18n';

const { t } = useI18n();
const props = defineProps({ user: Object });
const alertStore = useAlertStore();

async function changeAdminValue() {
        try {
            const res = await axios.post(
            '/api/change-admin-status/',
            { 
                id : props.user.id
            },
            {
            withCredentials: true
        });

        props.user.is_staff = res.data.newAdminStatus;

        if (res.data.newAdminStatus) {
          alertStore.showAlert(0, t('message.admin_luotu'));
        }
        else {
          // api call removes all admin rights
          props.user.is_superuser = res.data.newAdminStatus; 
          alertStore.showAlert(0, t('message.admin_poistettu'));
        }
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
<div class="admin-container">
  <div class="modal-buttons" v-if="props.user && props.user?.is_staff">
    <button class="btn btn-primary" @click="changeAdminValue">
      {{ props.user.is_staff ? t('message.poista_oikeudet') : t('message.tee_admin') }}
    </button>
  </div>
    <div class="modal-buttons" v-else>
    <button class="btn btn-primary" @click="changeAdminValue">{{ t('message.tee_admin') }}
    </button>
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

.modal-buttons button {
  margin-top: 1rem;
}

</style>