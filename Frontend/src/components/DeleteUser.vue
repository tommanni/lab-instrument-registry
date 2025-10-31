<script setup>
import axios from 'axios';
import { useAlertStore } from '@/stores/alert';
import { useI18n } from 'vue-i18n';
import { useRouter } from 'vue-router';

const { t } = useI18n();
const props = defineProps({ user: Object });
const alertStore = useAlertStore();
const router = useRouter()

async function deleteUser() {
        try {
            const res = await axios.post(
            '/api/delete-user/',
            { 
                id : props.user.id
            },
            {
            withCredentials: true
            });

            alertStore.showAlert(0, t('message.kayttaja_poistettu'));
            
            router.push('/admin/users'); // navigate back to user list after deletion

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
<div class="deletion-container">
  <div class="modal-buttons" v-if="props.user">
    <button class="btn btn-secondary" @click="deleteUser">
      {{t('message.poista_kayttaja')}}
    </button>
  </div>
</div>
</template>

<style scoped>

.deletion-container {
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
  background-color: #dc3545;
  color:#f4f4f8;
}



</style>