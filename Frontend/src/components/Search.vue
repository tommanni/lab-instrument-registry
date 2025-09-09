<script setup>
import { ref } from 'vue';
import { useDataStore } from '@/stores/data';

const store = useDataStore();
const searchTerm = ref('');

const performSearch = () => {
    store.searchData(searchTerm.value);
};

</script>

<template>
    <div class="search-container">
        <input v-model="searchTerm" :placeholder="$t('message.placeholder')" @keyup.enter="performSearch" />
        <button @click="performSearch">{{$t('message.haku_painike')}}</button>
    </div>
</template>

<style scoped>
.search-container {
    display: flex;
    align-items: top;
    justify-content: flex-start;
    padding-left: 10px;
}

input {
    width: 150px;
    height: 35px;
    padding: 5px;
}

button {
  padding: 5px 10px;  /* Keep padding controlled */
  padding-right: 10px;
  background-color: #4E008E;
  color: white;
  border: none;
  cursor: pointer;
  border-radius: 5px;
  text-align: center;
  white-space: nowrap; /* Prevent text from wrapping */
}
button:hover {
  background-color: #ab9bcb;
}
</style>
