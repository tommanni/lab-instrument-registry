<script setup>
import { useAlertStore } from '@/stores/alert'
const store = useAlertStore()
</script>

<template>
  <div class="about">
    <h1>This is a palceholder page for the users that will surely be implemented at some point</h1>
    <button @click="store.showAlert(1)">failure alert</button>
    <button @click="store.showAlert(0)">success alert</button>
  </div>
</template>

<style>
</style>
