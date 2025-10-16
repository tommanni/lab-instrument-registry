<script setup>
import axios from 'axios';
import UserInfo from '@/components/UserInfo.vue';
import ChangeAdminStatus from '@/components/ChangeAdminStatus.vue';
import ChangeActiveStatus from '@/components/ChangeActiveStatus.vue';
import ChangePassword from '@/components/ChangePassword.vue';
import { useDataStore } from '@/stores/data';
import { useUserStore } from '@/stores/user';
import { useAlertStore } from '@/stores/alert';
import { useI18n } from 'vue-i18n';
import { useRoute } from 'vue-router';
import { ref, onMounted, watch } from 'vue';


const { t } = useI18n();
const userStore = useUserStore();
const dataStore = useDataStore();
const alertStore = useAlertStore();
const route = useRoute();
const user = ref(null);
const loading = ref(true);

async function fetchUser(id) {
  if (!id) return;
  // Fetch user data by id
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
  } finally {
    loading.value = false;
  }
}

onMounted(() => fetchUser(route.params.id));

watch(
  // Refetch user data when route id param changes 
  // (e.g. when navigating to 'my information' from another user's info page)
  () => route.params.id,
  (new_id, old_id) => {
    if (new_id !== old_id) {
      fetchUser(new_id)
    }
  }
)
</script>

<template>
  <!-- Nothing is rendered on screen until loading state is false -->
  <main v-if="!loading">
    <template v-if="dataStore.isLoggedIn && userStore.user && 
    ( userStore.user.id === user?.id ||  userStore.user.is_superuser )">
      <h1 class="text-center"> {{ t('message.kayttaja_tietoja') }} </h1>

        <!-- Warning for admins editing someone else's information -->
        <div v-if="userStore.user && user && userStore.user.is_superuser && 
        userStore.user.id !== user.id" class="admin-warning">
        {{ t('message.tietojen_muokkaus_varoitus') }}
        </div>
        
      <div class="user-info-wrapper">
        <UserInfo :user="user"/>
      </div>
      
      <div class="change-password">
        <ChangePassword :user="user"/>
      </div>

      <div class="make-admin" v-if=" userStore.user && user &&  userStore.user.is_superuser && 
       userStore.user.id !== user.id">
        <ChangeAdminStatus :user="user"/>
      </div>
      <div v-if=" userStore.user && user &&  userStore.user.is_superuser &&  userStore.user.id !== user.id" class="change-active">
        <ChangeActiveStatus :user="user"/>
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

.make-admin {
 
}

.admin-warning {
  max-width: 600px;
  width: fit-content; 
  margin: 20px auto;
  padding: 0.75rem;
  box-sizing: border-box;
  background-color: #dc3545;
  color:#f4f4f8;
  border-radius: 4px;

}




</style>