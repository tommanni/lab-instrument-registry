<script setup>
import axios from 'axios';
import { useAlertStore } from '@/stores/alert';
import { useI18n } from 'vue-i18n';

const { t } = useI18n();
const props = defineProps({ user: Object });
const alertStore = useAlertStore();
const emit = defineEmits(['update-user', 'close']);


async function changeSuperadminValue() {
        try {
            const res = await axios.post(
            '/api/change-superadmin-status/',
            { 
                id : props.user.id
            },
            {
            withCredentials: true
        });

        //props.user.is_superuser = res.data.newSuperadminStatus;
        
        const updatedUser = {
          ...props.user,
          is_superuser: res.data.newSuperadminStatus,
          // When removing superadmin, also remove admin rights
          is_staff: res.data.newSuperadminStatus ? props.user.is_staff : false
        };
        
        // send user update event to parent
        emit('update-user', updatedUser);

        if (res.data.newSuperadminStatus) {
          alertStore.showAlert(0, t('message.superadmin_luotu'));
        }
        else {
          // api call removes all admin rights
          alertStore.showAlert(0, t('message.admin_poistettu'));
        }
    } catch (error) {
        if (error.response && error.response.data && error.response.data.message) {
            alertStore.showAlert(1, t('message.virhe') + error.response.data.message);
        }
        else {
            alertStore.showAlert(1, t('message.tuntematon_virhe'));
        }
    } finally {
    //closing overlay
    emit('close');
    }
}
</script>

<template>
  <div class="admin-container">
    
    <div class="modal-buttons">
      <button class="btn btn-primary" @click="changeSuperadminValue">
        {{ props.user.is_superuser 
            ? t('message.poista_oikeudet') 
            : t('message.tee_superadmin') 
        }}
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