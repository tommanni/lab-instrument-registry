<script setup>
import { useContractStore } from '@/stores/contract';
import { ref, computed } from 'vue';

const store = useContractStore();

const changePage = (index) => {
  if (index < 1) {
    store.currentPage = 1
    store.updateVisibleData()
  } else if (index > store.numberOfPages) {
    store.currentPage = store.numberOfPages
    store.updateVisibleData()
  } else {
    store.currentPage = index
    store.updateVisibleData()
  }
}
const pagesToShow = computed(() => {
  const maxVisiblePages = 10;
  const pages = new Set([1, store.numberOfPages]);

  if (store.numberOfPages <= maxVisiblePages) {
    return Array.from({ length: store.numberOfPages }, (_, i) => i + 1);
  }

  let start = Math.max(2, store.currentPage - 2);
  let end = Math.min(store.numberOfPages - 1, store.currentPage + 6);

  if (store.currentPage < 5) {
    start = 2;
    end = maxVisiblePages - 2;
  } else if (store.currentPage > store.numberOfPages - 5) {
    start = store.numberOfPages - (maxVisiblePages - 3);
    end = store.numberOfPages - 1;
  }

  for (let i = start; i <= end; i++) {
    pages.add(i);
  }

  return [...pages].sort((a, b) => a - b);
});
</script>

<template>
  <nav aria-label="Page navigation data">
    <ul class="pagination">
      <li class="page-item" :class="{ 'disabled': store.currentPage === 1 }">
        <a class="page-link" href="#" @click.prevent="changePage(store.currentPage - 1)">{{$t('message.edellinen')}}</a>
      </li>

      <template v-for="(n, index) in pagesToShow" :key="n">
        <li class="page-item" :class="{ 'active': store.currentPage === n }">
          <a class="page-link" href="#" @click.prevent="changePage(n)">{{ n }}</a>
        </li>
        <li v-if="index < pagesToShow.length - 1 && pagesToShow[index + 1] > n + 1" class="page-item disabled">
          <span class="page-link">...</span>
        </li>
      </template>

      <li class="page-item" :class="{ 'disabled': store.currentPage === store.numberOfPages }">
        <a class="page-link" href="#" @click.prevent="changePage(store.currentPage + 1)">{{$t('message.seuraava')}}</a>
      </li>
    </ul>
  </nav>
</template>

<style scoped>
.page-item.active .page-link {
  background-color: #4E008E !important; /* Vaihda haluamasi väri */
  border-color: #4E008E !important; 
  color: white !important;
}

.page-item.disabled .page-link {
  color: gray !important; /* Teksti harmaaksi */
}

.page-link {
  color: #4E008E !important; /* Vaihda haluamasi väri */
}

.page-link:hover {
  color: #4E008E !important; /* Vaihda haluamasi hover-väri */
  background-color: #C3B9D7 !important; /* Vaihda taustaväri hoverilla */
  transition: 0.3s ease-in-out; /* Pehmeä siirtymä */
}
</style>