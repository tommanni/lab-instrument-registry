<script setup>
import axios from 'axios';
import { ref, onMounted } from 'vue';
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

        props.user.is_superuser = res.data.newAdminStatus;
        alertStore.showAlert(0, res.data.message);
        
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
<div v-if="props.user && props.user?.is_superuser">
  <button @click="changeAdminValue">
    {{ props.user.is_superuser ? 'Remove Admin' : 'Make Admin' }}
  </button>
</div>
<div v-else>
  <button @click="changeAdminValue">Make Admin</button>
</div>
</template>

<style scoped>
</style>