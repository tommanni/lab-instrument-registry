<script setup>
import { ref, onMounted } from 'vue';
import TokenOverlay from '@/components/TokenOverlay.vue';
import UserData from '@/components/UserData.vue';
import { useUserStore } from '@/stores/user';
import { useDataStore } from '@/stores/data';
import { useI18n } from 'vue-i18n'

const { t } = useI18n()

const userStore = useUserStore()
const dataStore = useDataStore()

onMounted(() => {
  userStore.fetchData()
})
</script>

<template>
  <main v-if="dataStore.isLoggedIn">
    <div class="admins">
      <h2>{{$t('message.adminteksti')}}</h2>
    </div>
    <p></p>
    <ul class="navbar-nav ms-auto mb-2 mb-lg-0">
      <li class="nav-item">
        <TokenOverlay />
      </li>
    </ul>
    <div class="admindata">
      <UserData />
    </div>
  </main>

  <main v-else>
    <h1 class="text-center"> {{ t('message.admin_ei_oikeuksia') }} </h1>
  </main>
</template>

<style scoped>
main {
  padding-top: 70px;
  padding-left: 20px;
}

.admins h2 {
  white-space: nowrap;
}

.nav-item {
  padding-right: 20px
}

.admindata {
  padding-top: 25px;
  padding-bottom: 88px;
  padding-right: 20px;
  grid-row-start: 2;
  grid-column: 1 / span 3;
}

</style>