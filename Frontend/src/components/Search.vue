<script setup>
import { ref, onMounted } from 'vue';
import { useDataStore } from '@/stores/data';

const store = useDataStore();
const searchTerm = ref('');

const performSearch = () => {
    store.searchData(searchTerm.value);
};

const clearSearch = () => {
    searchTerm.value = '';
    performSearch();
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
        <button v-if="searchTerm" class="btn text-muted mx-1 clear-button" @click="clearSearch" data-bs-toggle="tooltip" :title="$t('message.nollaa_haku')">
            <i class="bi bi-x text-primary"></i>
        </button>
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
    width: 80%;
}

.search-container .btn {
    border-top-right-radius: 8px;
    border-bottom-right-radius: 8px;
    margin-left: 0 !important;
}

.clear-button {
    width: 32px;
    height: 42px;
    display: flex;
    align-items: center;
    border: none;
    padding: 0.5rem;
    font-size: 2.0rem;
}

.clear-button:hover i {
    color: #dc3545 !important;
}
</style>
