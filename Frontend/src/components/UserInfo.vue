<script setup>
import { useI18n } from 'vue-i18n';

const { t } = useI18n();
const props = defineProps({ user: Object });

</script>

<template>
  <div v-if="props.user">
    <h2>{{ props.user.full_name }}</h2>
    <p>{{ props.user.email }}</p>
  </div>
</template>

<style scoped>
</style>