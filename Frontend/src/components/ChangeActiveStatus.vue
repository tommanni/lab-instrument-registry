<script setup>
import axios from 'axios';
import { useAlertStore } from '@/stores/alert';
import { useI18n } from 'vue-i18n';

const { t } = useI18n();
const props = defineProps({ user: Object });
const alertStore = useAlertStore();

async function changeActiveValue() {
        try {
            const res = await axios.post(
            '/api/change-active-status/',
            { 
                id : props.user.id
            },
            {
            withCredentials: true
        });

        props.user.is_active = res.data.newActiveStatus;

        if (res.data.newActiveStatus) {
          alertStore.showAlert(0, t('message.käyttäjä_aktivoitu'));
        }
        else {
          alertStore.showAlert(0, t('message.käyttäjä_deaktivoitu'));
        }
    } catch (error) {
        if (error.response && error.response.data && error.response.data.detail) {
            alertStore.showAlert(1, t('message.virhe') + error.response.data.detail);
        }
        else {
            alertStore.showAlert(1, t('message.tuntematon_virhe'));
        }
    }
}
</script>

<template>
<div class="deactivation-container">
  <div class="modal-buttons" v-if="props.user && props.user?.is_active">
    <button class="btn btn-secondary" @click="changeActiveValue">
      {{ props.user.is_active ? t('message.deaktivoi_kayttaja') : t('message.aktivoi_kayttaja') }}
    </button>
  </div>
  <div class="modal-buttons" v-else>
    <button class="btn btn-secondary" @click="changeActiveValue">{{t('message.aktivoi_kayttaja')}}</button>
  </div>
</div>




</template>

<style scoped>

.deactivation-container {
  max-width: 600px;
  width: 100%;
  margin: 20px auto;
  padding: 1rem;
  box-sizing:border-box;

}

.modal-buttons button {
  margin-top: 1rem;
  border-radius: 4px;
  border: none;
  padding: 5px 10px;
}



</style>