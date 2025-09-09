<script setup>
import axios from 'axios';
import { computed, ref } from 'vue';
import { useAlertStore } from '@/stores/alert';
import { useDataStore } from '@/stores/data'
import { useUserStore } from '@/stores/user';
import { useI18n } from 'vue-i18n';

const { t, tm } = useI18n();
const dataStore = useDataStore();
const userStore = useUserStore();
const alertStore = useAlertStore()

const visible = ref(false)
const tokenOverlay = ref(false)
const clickedObject = ref({})
const showDeleteConfirmation = ref(false);
const clickedToken = ref(false)

const openTokenOverlay = () => {
  console.log("Opened token overlay");
  visible.value = true
}

const closeOverlay = () => {
  visible.value = false
}
</script>

<template>
  <div class="table-container">
    <table>
      <colgroup>
        <col v-for="(key, index) in $tm('userTableHeaders')" :key="key" />
      </colgroup>
      <thead>
        <tr>
          <th v-for="(key, index) in $tm('userTableHeaders')" :key="key">{{ key }}</th>
        </tr>
      </thead>

      <tbody>
        <tr v-for="(item, index) in userStore.currentData" :key="index">
          <td>
            {{ item.full_name }}
          </td>
          <td>
            {{ item.email }}
          </td>
        </tr>
      </tbody>
    </table>
  </div>
</template>

<style scoped>
.overlay-backdrop {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background-color: rgba(0, 0, 0, 0.5);
  z-index: 1031;
}
.overlay-content {
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  background: #fff;
  padding: 2em;
  border-radius: 4px;
  box-shadow: 0 2px 10px rgba(0, 0, 0, 0.3);
  z-index: 1032;
}
.close-button {
  position: absolute;
  top: 0.5em;
  right: 0.5em;
  background: transparent;
  border: none;
  font-size: 1.4rem;
  cursor: pointer;
  line-height: 1;
}
.close-button:hover {
  color: #b00;
}
.buttons {
  margin-top: 15px;
  display: flex;
  justify-content: space-between;
}
.btn {
  padding: 5px 10px;
  border: none;
  cursor: pointer;
  border-radius: 5px;
}
.btn-delete {
  background: #4E008E;
  color: white;
}
.btn-delete:hover {
  background-color: #ab9bcb;
}
.btn-cancel {
  background-color: rgb(158, 158, 158);
  color: white;
}
.btn-cancel:hover {
  background-color: #cacaca;
}
.btn-update {
  background: #cf286f;
  color: white;
}
.btn-update:hover {
  background-color: #F5A5C8;
}
.modal-buttons {
  margin-top: 15px;
  display: flex;
  justify-content: space-around;
}

.table-container {
  width: 100%;
  overflow-x: auto;
}

table {
  width: 100%;
  border-collapse: collapse;
  table-layout: fixed;
}

th, td {
  border: 1px solid #ddd;
  padding: 8px;
  position: relative;
  text-align: left;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

th {
  background: #f4f4f4;
  position: relative;
}

.resizer {
  position: absolute;
  right: 0;
  top: 0;
  width: 5px;
  height: 100%;
  cursor: col-resize;
  background: transparent;
}

.resizer:hover {
  background: #ab9bcb;
}
</style>