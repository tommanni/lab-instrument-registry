<script setup>
import logo_TAU from '@/assets/logo_TAU.svg'
</script>

<template>
    <footer class="footer fixed-bottom">
        <img :src="logo_TAU" alt="tuni_logo" class="footer-logo"/>
    </footer>
</template>

<style scoped>
.footer {
    width: 100%;
    background-color: #ffffff;
    color: #ffffff;
    position: fixed;
    bottom: 0;
}

.footer-logo {
    max-height: 80px;
    margin-bottom: 0.5rem;
}
</style>