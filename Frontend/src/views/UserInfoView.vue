<script setup>
import axios from 'axios';
import UserInfo from '@/components/UserInfo.vue';
import ChangeAdminStatus from '@/components/ChangeAdminStatus.vue';
import ChangePassword from '@/components/ChangePassword.vue';
import { useDataStore } from '@/stores/data';
import { useAlertStore } from '@/stores/alert';
import { useI18n } from 'vue-i18n';
import { useRoute } from 'vue-router';
import { ref, onMounted } from 'vue';


const { t } = useI18n();
const dataStore = useDataStore();
const alertStore = useAlertStore();
const route = useRoute();
const user = ref(null);
const current_user = ref(null);
const loading = ref(true); // <-- new loading flag

async function fetchUsers(id) {
  if (!id) return;

  try {
    const res = await axios.get(`/api/users/${id}/`, {
      withCredentials: true
    })
    user.value = res.data;
  } catch (error) {
        if (error.response && error.response.data && error.response.data.detail) {
            alertStore.showAlert(1, t('message.virhe') + error.response.data.detail);
        }
        else {
            alertStore.showAlert(1, t('message.tuntematon_virhe'));
        }
  }

  try {
    const res = await axios.get(`/api/users/${'me'}/`, {
      withCredentials: true
    })
    current_user.value = res.data;
  } catch (error) {
        if (error.response && error.response.data && error.response.data.detail) {
            alertStore.showAlert(1, t('message.virhe') + error.response.data.detail);
        }
        else {
            alertStore.showAlert(1, t('message.tuntematon_virhe'));
        }
  } finally {
    loading.value = false;
  }
}

onMounted(() => fetchUsers(route.params.id));
</script>

<template>
  <!-- Nothing is rendered on screen until loading state is false -->
  <main v-if="!loading">
    <template v-if="dataStore.isLoggedIn && current_user && ( current_user.id === user?.id || current_user.is_superuser)">
      <h1 class="text-center"> {{ t('message.kayttaja_tietoja') }} </h1>

      <!-- Warning for admins editing someone else's information -->
      <div v-if="current_user && user && current_user.is_superuser && current_user.id !== user.id" class="admin-warning">
        {{ t('message.tietojen_muokkaus_varoitus') }}
      </div>
      


      <div class="userdata">
        <UserInfo :user="user"/>
      </div>
      <div class="change-password">
        <ChangePassword :user="user"/>
      </div>
      <div v-if="current_user && user && current_user.is_superuser && current_user.id !== user.id" class="change-admin">
        <ChangeAdminStatus :user="user"/>
      </div>
    </template>
    <template v-else>
      <h1 class="text-center"> {{ t('message.admin_ei_oikeuksia') }} </h1>
    </template>
  </main>
  
</template>

<style scoped>
main {
  padding-top: 70px;
  padding-left: 20px;
}
.userdata {
  max-width: 600px;
  width: 100%; 
  margin: 20px auto;
  padding: 1rem;
  box-sizing: border-box;
}

.change-password {
  margin-top: 20px;
  margin-bottom: 20px;
}

.admin-warning {
  position: absolute;
  top: 80px;
  left: 60%;
  transform: translateX(-50%);
  background-color: #ffc3c3;
  color: #7e1b1b;
  padding: 8px 15px;
  border-radius: 6px;
  font-weight: 500;
  z-index: 10;
}


.change-admin {
  margin-top: 100px;
  margin-bottom: 20px;
  margin-left: 250px;
}
</style>