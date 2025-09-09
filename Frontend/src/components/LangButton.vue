<script setup>
import { useI18n } from 'vue-i18n';

const { t, locale } = useI18n()

function changeLanguage(lang) {
    locale.value = lang
}
</script>

<template>
    <div class="lang-buttons">
        <button 
        @click="changeLanguage('fi')"> Suomi </button>
        <button
        @click="changeLanguage('en')"> English </button>
        
    </div>
</template>

<style scoped>
.lang-buttons {
    margin-top: 7px;
}

.lang-buttons button {
    margin-right: 8px;
    background-color: #4E008E;
    color: white;
    border: none;
    cursor: pointer;
    border-radius: 5px;
    text-align: center;
    white-space: nowrap;
    padding: 5px;
    padding-left: 7px;
    padding-right: 7px;
}

.lang-buttons button:hover {
    background-color: #ab9bcb;
}
</style>