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
        <button class="btn" @click="changeLanguage('fi')"> FI </button>
        <button class="btn" @click="changeLanguage('en')"> EN </button>

    </div>
</template>

<style scoped>
.lang-buttons {
    display: grid;
    grid-template-columns: 1fr 1fr;
}
</style>