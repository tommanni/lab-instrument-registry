<script setup>
import { ref, onMounted, onBeforeUnmount, watch, nextTick } from 'vue';
import { Popover } from 'bootstrap';
import { useI18n } from 'vue-i18n';

const { t } = useI18n();
const searchTerm = ref('');

const props = defineProps({
  searchFunction: Function,
  cookieName: String
})

const infoButtonRef = ref(null);

const performSearch = () => {
   props.searchFunction(searchTerm.value);
};

const clearSearch = () => {
    searchTerm.value = '';
    performSearch();
};

const { locale } = useI18n();

let popoverInstance = null;

const initPopover = () => {
  if (infoButtonRef.value) {
    popoverInstance = new Popover(infoButtonRef.value, { trigger: 'hover focus', container: 'body' });
  }
};

onMounted(() => {
  const match = document.cookie.match(new RegExp(`${props.cookieName}=([^;]+)`));
  if (match) {
    searchTerm.value = decodeURIComponent(match[1]);
  }

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
        <button ref="infoButtonRef" type="button" class="btn text-muted mx-1 info-button" aria-label="Hakuohje"
                data-bs-toggle="popover" data-bs-placement="bottom" data-bs-trigger="hover focus"
                :title="$t('message.haku_info_title')" :data-bs-content="$t('message.haku_info_content')">
            <i class="bi bi-info-circle text-primary"></i>
        </button>
    </div>
</template>

<style scoped>
.search-container {
    display: inline-flex;
    align-items: center;
    justify-content: space-between;
    gap: .3rem; /*Gap for input focus borders not to clip */
    max-width: 600px;
}

.form-control {
    height: 100%;
    width: 300px;
    padding-right:3.5rem;
}

.input-wrapper {
    position: relative;
    width:100%;
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

.info-button {
    width: 32px;
    height: 42px;
    display: flex;
    align-items: center;
    border: none;
    padding: 0.5rem;
    font-size: 1.4rem;
}
</style>
