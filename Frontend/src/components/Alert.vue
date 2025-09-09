<script setup>
import { useAlertStore } from '@/stores/alert'
const store = useAlertStore()
</script>

<template>
    <template v-if="store.visibility">
        <div v-if="store.alertType === 0" @click="store.visibility = false" class="alert alert-success" role="alert">
            {{ store.alertText }}
        </div>
        <div v-else-if="store.alertType === 1" @click="store.visibility = false" class="alert alert-danger" role="alert">
            {{ store.alertText }}
        </div>
    </template>
</template>

<style scoped>
.alert {
    width: 30vw;
    height: 5vh;
    position: fixed;
    z-index: 9999;
    top: 70px;
    left: 25%;
}
</style>