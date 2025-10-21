<script setup>
import { useI18n } from 'vue-i18n';

const { t, locale } = useI18n()

function changeLanguage(lang) {
    locale.value = lang
    const maxAge = 60 * 60 * 24 * 365 * 10; // 10 years
    // TODO add commented parameters to cookie definition for live build HTTPS
    document.cookie = 'Language=' + lang + '; Max-Age=' + maxAge + '; path=/' /*; Secure; SameSite=Strict'; */
}
</script>

<template>
    <div class="lang-buttons">
        <button class="btn"
        :class="{ selected: locale === 'fi' || locale === ''}" 
        @click="changeLanguage('fi')"> FI 
        </button>
        <button class="btn" 
        :class="{ selected: locale === 'en'}"
        @click="changeLanguage('en')"> EN 
        </button>

    </div>
</template>

<style scoped>
.lang-buttons {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 0.5 rem;
}

.btn {
  position: relative;
  padding: 0.5rem 1rem;
  background: transparent;
  border: none;
  cursor: pointer;
  z-index: 1;
  overflow: hidden;
}

.btn::before {
  content: '';
  position: absolute;
  top: 50%;
  left: 50%;
  width: 2rem;
  height: 2rem;
  background-color: var(--bs-primary);
  border-radius: 50%;
  transform: translate(-50%, -50%) scale(0);
  transition: transform 0.3s ease;
  z-index: -1;
}

.btn:hover::before,
.btn.selected::before {
  transform: translate(-50%, -50%) scale(1);
}

.btn:hover,
.btn.selected {
  color: white;
}
</style>