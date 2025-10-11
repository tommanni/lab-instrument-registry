<script setup>
import { ref, onMounted } from 'vue';

const searchTerm = ref('');

const props = defineProps({
  searchFunction: Function,
  cookieName: String
})

const performSearch = () => {
   props.searchFunction(searchTerm.value);
};

const clearSearch = () => {
    searchTerm.value = '';
    performSearch();
};

// Check for active search terms on page load
onMounted(() => {
  const match = document.cookie.match(new RegExp(`${props.cookieName}=([^;]+)`));
  if (match) {
    searchTerm.value = decodeURIComponent(match[1]);
  }
});

</script>

<template>
    <div class="search-container">
        <div class="input-wrapper">
            <input class="form-control" v-model="searchTerm" :placeholder="$t('message.placeholder')" @keyup.enter="performSearch" />
            <a v-if="searchTerm" class="text-muted mx-1 clear-button fs-5" @click="clearSearch" data-bs-toggle="tooltip" :title="$t('message.nollaa_haku')">
                <i class="bi bi-x text-primary"></i>
            </a>
        </div>
        <button class="btn btn-primary" @click="performSearch">{{$t('message.haku_painike')}}</button>
    </div>
</template>

<style scoped>
.search-container {
    display: flex;
    align-items: top;
    justify-content: space-between;
    gap: .3rem; /*Gap for input focus borders not to clip */
    max-width: 600px;
}

.input-wrapper {
    position: relative;
    flex: 1;
}

/*input {
    width: 150px;
    height: 35px;
    padding: 5px;
    width: 100%;
    height: 40px;
    overflow: hidden;
}*/

.search-container .form-control {
    border-top-left-radius: var(--bs-border-radius-lg);
    border-bottom-left-radius: var(--bs-border-radius-lg);
    border-collapse: collapse;
    padding-right: 1.8rem; /*room for the clear button */
    box-sizing: border-box;
}

.search-container .btn {
    border-top-right-radius: var(--bs-border-radius-lg);
    border-bottom-right-radius: var(--bs-border-radius-lg);
}

.clear-button {
    display: flex;
    align-items: center;
    padding: 0;
    cursor: pointer;
    position: absolute;
    top: 50%;
    right: 0;
    transform: translateY(-50%);
}

.clear-button:hover i {
    color: #dc3545 !important;
}
</style>
