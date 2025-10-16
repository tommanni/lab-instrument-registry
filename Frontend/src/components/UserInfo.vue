<script setup>
import { useI18n } from 'vue-i18n';

const { t } = useI18n();
const props = defineProps({ user: Object });

</script>

<template>
  <div class="user-info-container" props.user>
    <h2>{{ props.user.full_name }}</h2>
    <p>{{ props.user.email }}</p>
  </div>
</template>

<style scoped>

.user-info-container {
  max-width: 600px;
  width: 100%; 
  margin: 20px auto;
  padding: 1rem;
  box-sizing: border-box;
}

</style>