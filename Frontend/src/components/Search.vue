<script setup>
import { useDataStore } from '@/stores/data';
import { useUserStore } from '@/stores/user';
import { ref, onMounted, onBeforeUnmount, watch, nextTick } from 'vue';
import { Popover } from 'bootstrap';
import { useI18n } from 'vue-i18n';

const dataStore = useDataStore();
const userStore = useUserStore();

const props = defineProps({
  searchFunction: Function,
  searchType: String
})

const infoButtonRef = ref(null);

const clearSearch = () => {
    props.searchFunction(true);
};

const { locale } = useI18n();

let popoverInstance = null;

const initPopover = () => {
  if (infoButtonRef.value) {
    popoverInstance = new Popover(infoButtonRef.value, { trigger: 'hover focus', container: 'body' });
  }
};

onMounted(() => {
  initPopover();
});

onBeforeUnmount(() => {
  if (popoverInstance) {
    popoverInstance.dispose();
    popoverInstance = null;
  }
});

watch(locale, async () => {
  if (popoverInstance) {
    popoverInstance.dispose();
    popoverInstance = null;
  }
  await nextTick();
  initPopover();
});

watch(() => dataStore.searchMode, async () => {
  if (popoverInstance) {
    popoverInstance.dispose();
    popoverInstance = null;
  }
  await nextTick();
  initPopover();
});

</script>

<template>
    <div v-if="searchType==='device'" class="search-container">
        <div class="input-wrapper">
            <input class="form-control" v-model="dataStore.searchTerm" :placeholder="dataStore.searchMode === 'direct' ? $t('message.placeholder') : $t('message.placeholder_smart_search')" @keyup.enter="searchFunction(false)" />
            <a v-if="dataStore.searchTerm" class="text-muted mx-1 clear-button fs-5" @click="clearSearch" data-bs-toggle="tooltip" :title="$t('message.nollaa_haku')">
                <i class="bi bi-x text-primary"></i>
            </a>
        </div>
        <div class="btn-group search-mode-selector" role="group" aria-label="Search mode">
          <input type="radio" class="btn-check" name="searchModeDevice" id="direct-search-device" autocomplete="off" value="direct" v-model="dataStore.searchMode">
          <label class="btn btn-outline-primary" for="direct-search-device">{{$t('message.tarkka_haku')}}</label>

          <input type="radio" class="btn-check" name="searchModeDevice" id="smart-search-device" autocomplete="off" value="smart" v-model="dataStore.searchMode">
          <label class="btn btn-outline-primary" for="smart-search-device">{{$t('message.älykäs_haku')}}</label>
        </div>
        <button class="btn btn-primary" @click="searchFunction(false)">{{$t('message.haku_painike')}}</button>
        <button ref="infoButtonRef" type="button" class="btn text-muted mx-1 info-button" aria-label="Hakuohje"
                data-bs-toggle="popover" data-bs-placement="bottom" data-bs-trigger="hover focus"
                :title="$t('message.haku_info_title')" 
                :data-bs-content="dataStore.searchMode === 'direct' ? $t('message.haku_info_content') : $t('message.smart_search_info_content')"
        >
            <i class="bi bi-info-circle text-primary"></i>
        </button>
    </div>
    <div v-else-if="searchType==='user'" class="search-container">
        <div class="input-wrapper">
            <input class="form-control" v-model="userStore.searchTerm" :placeholder="$t('message.placeholder_user')" @keyup.enter="searchFunction(false)" />
            <a v-if="userStore.searchTerm" class="text-muted mx-1 clear-button fs-5" @click="clearSearch" data-bs-toggle="tooltip" :title="$t('message.nollaa_haku')">
                <i class="bi bi-x text-primary"></i>
            </a>
        </div>
        <button class="btn btn-primary" @click="searchFunction(false)">{{$t('message.haku_painike')}}</button>
    </div>
</template>

<style scoped>
.search-container {
    display: inline-flex;
    align-items: center;
    justify-content: space-between;
    gap: .3rem; /*Gap for input focus borders not to clip */
    width: 80%;
}

.search-mode-selector .btn {
  display: flex;
  align-items: center;
  justify-content: center;
}

.form-control {
    height: 100%;
    width: 100%;
    padding-right:3.5rem;

    padding: 7px;
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

.search-container {
    border-top-left-radius: var(--bs-border-radius-lg);
    border-bottom-left-radius: var(--bs-border-radius-lg);
    border-collapse: collapse;
    box-sizing: border-box;
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

.info-button {
    width: 32px;
    height: 42px;
    display: flex;
    align-items: center;
    border: none;
    padding: 0.5rem;
    font-size: 1.4rem;
}

@media screen and (max-width: 768px){
    .search-container {
        width: 100%;
        flex-wrap: wrap;
    }

    .search-mode-selector {
      width: 100%;
      justify-content: center;
    }
}
</style>
