<script setup>
import { ref, onMounted } from 'vue';
import { useDataStore } from '@/stores/data';

const store = useDataStore();
const searchTerm = ref('');

const performSearch = () => {
    store.searchData(searchTerm.value);
};

// Check for active search terms on page load
onMounted(() => {
  const match = document.cookie.match(/SearchTerm=([^;]+)/);
  if (match) {
    searchTerm.value = decodeURIComponent(match[1]);
  }
});

</script>

<template>
    <div class="search-container">
        <input class="form-control" v-model="searchTerm" :placeholder="$t('message.placeholder')" @keyup.enter="performSearch" />
        <button class="btn btn-primary ms-2" @click="performSearch">{{$t('message.haku_painike')}}</button>
    </div>
</template>

<style scoped>
.search-container {
    display: flex;
    width: 100%;
    height: 40px;
    border-radius: 8px;
    overflow: hidden;
}

.search-container .form-control {
    border-top-left-radius: 8px;
    border-bottom-left-radius: 8px;
    border-right: none;
}

.search-container .btn {
    border-top-right-radius: 8px;
    border-bottom-right-radius: 8px;
    margin-left: 0 !important;
}
</style>
