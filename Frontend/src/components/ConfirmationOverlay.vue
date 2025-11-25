<script setup>
import { useI18n } from 'vue-i18n';
import { useAlertStore } from '@/stores/alert';

const { t } = useI18n()
const alertStore = useAlertStore();

const props = defineProps({
  component: Object,
  user: Object,
  messageKey: String
});

const emit = defineEmits(['update-user', 'close']);


function closeOverlay() {
  emit('close');
}
</script>

<template>
  <div class="overlay-backdrop">
    <div class="overlay-content">
      <button type="button"
            class="btn-close position-absolute top-0 end-0 m-3"
            @click="closeOverlay"
            aria-label="Close"></button>

      <!-- Title -->
      <h3 class="overlay-message" style="margin-top: 1.5rem;">
        {{ t(props.messageKey) }}
      </h3>

      <!-- Render selected inner component -->
      <component
        v-if="props.component"
        :is="props.component"
        :user="props.user"
        @update-user="$emit('update-user', $event)"
        @close="closeOverlay"
      />
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

.overlay-backdrop {
  position: fixed;
  top: 0; left: 0; right: 0; bottom: 0;
  background-color: rgba(0,0,0,0.5);
  z-index: 1060;
}

.overlay-content {
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  background: #fff;
  padding: 2em;
  border-radius: 4px;
  box-shadow: 0 2px 10px rgba(0,0,0,0.3);
  max-width: 500px;
  width: 100%;
  box-sizing: border-box;
}

.modal-buttons button {
  margin-top: 1rem;
}



</style>