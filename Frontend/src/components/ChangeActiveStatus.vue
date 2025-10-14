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
<div v-if="props.user && props.user?.is_active">
  <button @click="changeActiveValue">
    {{ props.user.is_active ? 'Make Inactive' : 'Make Active' }}
  </button>
</div>
<div v-else>
  <button @click="changeActiveValue">Make Active</button>
</div>
</template>

<style scoped>
</style>