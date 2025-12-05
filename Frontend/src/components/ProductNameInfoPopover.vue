<script setup>
import { ref, onMounted, onBeforeUnmount, watch, nextTick } from 'vue';
import { useI18n } from 'vue-i18n';
import { Popover } from 'bootstrap';

const { t, locale } = useI18n();
const infoButtonRef = ref(null);
let popoverInstance = null;

const initPopover = () => {
  if (locale.value !== 'en') return;
  
  nextTick(() => {
    if (infoButtonRef.value) {
      // Dispose existing instance if any
      if (popoverInstance) {
        popoverInstance.dispose();
      }
      
      popoverInstance = new Popover(infoButtonRef.value, {
        trigger: 'hover focus',
        container: 'body',
        placement: 'bottom',
        html: false
      });
    }
  });
};

onMounted(() => {
  initPopover();
});

onBeforeUnmount(() => {
  if (popoverInstance) {
    popoverInstance.dispose();
    popoverInstance = null;
  }
});

watch(locale, async () => {
  if (popoverInstance) {
    popoverInstance.dispose();
    popoverInstance = null;
  }
  await nextTick();
  initPopover();
});
</script>

<template>
  <button v-if="locale === 'en'"
          ref="infoButtonRef"
          type="button"
          class="info-icon"
          @click.stop
          data-bs-toggle="popover"
          data-bs-placement="bottom"
          data-bs-trigger="hover focus"
          :title="t('message.ai_translation_warning_title')"
          :data-bs-content="t('message.ai_translation_warning_content')"
          aria-label="Translation warning">
    <i class="bi bi-info-circle text-primary"></i>
  </button>
</template>

<style scoped>
.info-icon {
  border: none;
  background: transparent;
  padding: 0;
  margin: 0 0 0 0.4rem;
  line-height: 1;
  height: auto;
  min-height: 0;
  vertical-align: middle;
  cursor: pointer;
  display: inline-block;
}

.info-icon i {
  font-size: 1.2rem;
}

.info-icon:hover,
.info-icon:focus {
  background: transparent;
  border: none;
  outline: none;
}

.info-icon:hover i {
  opacity: 0.7;
}
</style>

