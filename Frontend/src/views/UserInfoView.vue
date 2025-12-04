<script setup>
import axios from 'axios';
import UserInfo from '@/components/UserInfo.vue';
import PasswordOverlay from '@/components/PasswordOverlay.vue';
import ConfirmationOverlay from '@/components/ConfirmationOverlay.vue';
import ChangeAdminStatus from '@/components/ChangeAdminStatus.vue';
import ChangeSuperadminStatus from '@/components/ChangeSuperadminStatus.vue';
import DeleteUser from '@/components/DeleteUser.vue';

import { useDataStore } from '@/stores/data';
import { useUserStore } from '@/stores/user';
import { useI18n } from 'vue-i18n';
import { useRoute } from 'vue-router';
import { ref, onMounted, watch } from 'vue';
import { useAlertStore } from '@/stores/alert';
import { computed } from 'vue';

const { t } = useI18n();
const userStore = useUserStore();
const dataStore = useDataStore();
const route = useRoute();
const user = ref(null);
const loading = ref(true);
const alertStore = useAlertStore();


// Confirmation overlay state
const showOverlay = ref(false);
const selectedUser = ref(null);
const currentMessageKey = ref('');
const currentAction = ref('');

// Mapping of actions to components
const actionComponents = {
  admin: ChangeAdminStatus,
  superadmin: ChangeSuperadminStatus,
  delete: DeleteUser
};

// Compute which component will be shown in overlay
const currentComponent = computed(() => actionComponents[currentAction.value]);


function handleUserUpdate(updatedUser) {
  user.value = { ...updatedUser };
}

function openConfirmation(userObj, actionType) {
  selectedUser.value = userObj;
  currentAction.value = actionType;
  showOverlay.value = true;
  
  switch(actionType) {
    case 'admin':
      currentMessageKey.value = userObj.is_staff
        ? 'message.haluatko_poistaa_adminin'
        : 'message.haluatko_tehda_adminin';
      break;

    case 'superadmin':
      currentMessageKey.value = userObj.is_superuser
        ? 'message.haluatko_poistaa_adminin'
        : 'message.haluatko_tehda_superadminin';
      break;

    case 'delete':
      currentMessageKey.value = 'message.haluatko_poistaa_kayttajan';
      break;
  }

}

function closeOverlay() {
  showOverlay.value = false;
}


async function fetchUser(id) {
  if (!id) return;
  // Fetch user data by id
  try {
    const res = await axios.get(`/api/users/${id}/`, {
      withCredentials: true
    })
    user.value = res.data;
  } catch (error) {
    if (!dataStore.user.is_staff) return;

    const msg = error.response?.data?.detail || t('message.tuntematon_virhe');
    alertStore.showAlert(1, t('message.virhe') + msg);
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
    <template v-if="dataStore.isLoggedIn && userStore.user && user &&
    ( userStore.user.id === user.id || userStore.user.is_staff || userStore.user.is_superuser )">
      
      <h2 class="text-center"> {{ t('message.kayttaja_tietoja') }} </h2>

      <!-- Warning for admins editing someone else's information -->
      <div v-if="userStore.user && user && 
        userStore.user.id !== user.id" class="admin-warning">
        {{ t('message.tietojen_muokkaus_varoitus') }}
      </div>
        
      <div class="user-info-wrapper">
        <UserInfo :user="user"/>
      </div>
      
      <!-- Password overlay -->
      <div class="password-container" v-if="userStore.user && user &&  
       ( userStore.user.id === user.id || userStore.user.is_superuser || !user.is_superuser )">
          <PasswordOverlay :user="user"/>
      </div>

      <!-- Admin stuff -->
      <h3 class="admin-info-wrapper" v-if="userStore.user && user && userStore.user.is_superuser && userStore.user.id !== user.id">
        {{t('message.adminteksti')}}
      </h3>

      <div class="action-buttons-container" v-if="userStore.user && user &&  userStore.user.is_superuser && 
       userStore.user.id !== user.id">
          
          <!-- If user is superadmin: show only "Remove admin" button -->
          <template v-if="user.is_superuser">
            <button class="btn btn-primary me-2" @click="openConfirmation(user, 'superadmin')">
              {{ t('message.poista_oikeudet') }}
            </button>
          </template>

          <!-- If user is admin (but not superadmin): show both remove admin and make superadmin buttons -->
          <template v-else-if="user.is_staff">
            <button class="btn btn-primary me-2" @click="openConfirmation(user, 'admin')">
              {{ t('message.poista_oikeudet') }}
            </button>
            <button class="btn btn-primary me-2" @click="openConfirmation(user, 'superadmin')">
              {{ t('message.tee_superadmin') }}
            </button>
          </template>

          <!-- If user is regular user: show make admin and make superadmin buttons -->
          <template v-else>
            <button class="btn btn-primary me-2" @click="openConfirmation(user, 'admin')">
              {{ t('message.tee_admin') }}
            </button>
            <button class="btn btn-primary me-2" @click="openConfirmation(user, 'superadmin')">
              {{ t('message.tee_superadmin') }}
            </button>
          </template>

          <!-- Delete user button (always shown) -->
          <button class="btn btn-danger" @click="openConfirmation(user, 'delete')">
            {{ t('message.poista_kayttaja') }}
          </button>
        </div>

      <!-- Confirmation overlay, shows current action component -->
      <ConfirmationOverlay
      v-if="showOverlay"
      :component="currentComponent"
      :user="selectedUser"
      :message-key="currentMessageKey"
      @close="closeOverlay"
      @update-user="handleUserUpdate"
      />
    </template>

    <template v-else-if="userStore.user && !user &&  userStore.user.is_superuser">
      <h1 class="text-center"> {{ t('message.kayttajaa_ei_olemassa') }} </h1>
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


.password-container {
  max-width: 600px;
  width: 100%; 
  margin: 20px auto;
  padding: 1rem;
  box-sizing: border-box;
}

.admin-info-wrapper {
  max-width: 600px;
  width: 100%; 
  margin: 20px auto;
  padding: 1rem;
  box-sizing: border-box;
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

.action-buttons-container {
  max-width: 600px;
  width: 100%; 
  margin: 20px auto;
  padding: 1rem;
  box-sizing: border-box;
}

.delete-button {
  display: flex;
  justify-content: flex-start;
}

</style>
