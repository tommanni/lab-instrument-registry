<script setup>
import { computed, ref } from 'vue';
import { useRouter } from 'vue-router'
import { useDataStore } from '@/stores/data'
import { useUserStore } from '@/stores/user';
import { useI18n } from 'vue-i18n';

const { t, tm } = useI18n();
const dataStore = useDataStore();
const userStore = useUserStore();
const router = useRouter();

const sortKey = ref(null);
const sortOrder = ref('asc');

const headerMap = {
  [tm('userTableHeaders')[0]] : 'full_name',
  [tm('userTableHeaders')[1]] : 'email',
  [tm('userTableHeaders')[2]] : 'is_staff',
  [tm('userTableHeaders')[3]] : 'is_superuser',
};

function sortBy(key) {
  if (sortKey.value === key) {
    sortOrder.value = sortOrder.value === 'asc' ? 'desc' : 'asc';
  } else {
    sortKey.value = key;
    sortOrder.value = 'asc';
  }
}

const sortedData = computed(() => {
  if (!sortKey.value) return userStore.currentData;

  return [...userStore.currentData].sort((a, b) => {
    let aVal = a[sortKey.value];
    let bVal = b[sortKey.value];

    if (typeof aVal === 'boolean' && typeof bVal === 'boolean') {
      // For admin values, reverse logic so 'X' appears first in ascending order
      return sortOrder.value === 'asc' ? bVal - aVal : aVal - bVal;
    }

    if (typeof aVal === 'string') aVal = aVal.toLowerCase();
    if (typeof bVal === 'string') bVal = bVal.toLowerCase();

    if (aVal < bVal) return sortOrder.value === 'asc' ? -1 : 1;
    if (aVal > bVal) return sortOrder.value === 'asc' ? 1 : -1;
    return 0;
  });
});

function goToUser(id) {
  router.push({ name: 'UserInfoView', params: { id } })
}
</script>

<template>
  <div v-if="dataStore.isLoggedIn && userStore.user && 
  (userStore.user.is_staff || userStore.user.is_superuser)" 
  class="table-container">
    <table>
      <colgroup>
          <col v-for="(key, index) in $tm('userTableHeaders')"
            :key="key"
            :style="{
              width: index < 2 ? '40%' : '7%'
            }"
          />
      </colgroup>
      
      <thead>
        <tr>
          <th
            v-for="(key, index) in $tm('userTableHeaders')"
            :key="key"
            @click="sortBy(headerMap[key])"
            style="cursor: pointer;"
          >
            {{ key }}
            <span v-if="sortKey === headerMap[key]">
              {{ sortOrder === 'asc' ? '↓' : '↑' }}
            </span>
          </th>
        </tr>
      </thead>

      <tbody>
        <tr
          v-for="(item, index) in sortedData"
          :key="index"
          @click="goToUser(item.id)"
          style="cursor: pointer;"
        >
          <td>{{ item.full_name }}</td>
          <td>{{ item.email }}</td>
          <td>{{ item.is_staff ? 'X' : '' }}</td>
          <td>{{ item.is_superuser ? 'X' : '' }}</td>
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
  margin-top: 5px;
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