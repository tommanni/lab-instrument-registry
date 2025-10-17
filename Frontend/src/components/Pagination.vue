<script setup>
import { useDataStore } from '@/stores/data';
import { computed } from 'vue';
import { useI18n } from 'vue-i18n';

const { t, tm } = useI18n();

const props = defineProps({
  store: {
    type: Object,
    default: null
  }
});

// Use provided store or default to dataStore
const activeStore = props.store || useDataStore();

const changePage = (index) => {
  if (index < 1) {
    activeStore.currentPage = 1
    activeStore.updateVisibleData()
  } else if (index > activeStore.numberOfPages) {
    activeStore.currentPage = activeStore.numberOfPages
    activeStore.updateVisibleData()
  } else {
    activeStore.currentPage = index
    activeStore.updateVisibleData()
  }
}
const pagesToShow = computed(() => {
  const maxVisiblePages = 10;
  const pages = new Set([1, activeStore.numberOfPages]);

  if (activeStore.numberOfPages <= maxVisiblePages) {
    return Array.from({ length: activeStore.numberOfPages }, (_, i) => i + 1);
  }

  let start = Math.max(2, activeStore.currentPage - 2);
  let end = Math.min(activeStore.numberOfPages - 1, activeStore.currentPage + 6);

  if (activeStore.currentPage < 5) {
    start = 2;
    end = maxVisiblePages - 2;
  } else if (activeStore.currentPage > activeStore.numberOfPages - 5) {
    start = activeStore.numberOfPages - (maxVisiblePages - 3);
    end = activeStore.numberOfPages - 1;
  }

  for (let i = start; i <= end; i++) {
    pages.add(i);
  }

  return [...pages].sort((a, b) => a - b);
});
</script>
<template>
  <nav aria-label="Page navigation data" class="d-flex justify-content-center align-items-center my-3">
    <ul class="pagination mb-0">
      <li class="page-item" :class="{ 'disabled': activeStore.currentPage === 1 }">
        <a class="page-link" href="#" @click.prevent="changePage(activeStore.currentPage - 1)" aria-label="Previous">
          <span aria-hidden="true">&laquo;</span>
          <span class="ms-1 d-none d-sm-inline">{{t('message.edellinen')}}</span>
        </a>
      </li>

      <template v-for="(n, index) in pagesToShow" :key="n">
        <li class="page-item" :class="{ 'active': activeStore.currentPage === n }">
          <a class="page-link" href="#" @click.prevent="changePage(n)">
            {{ n }}
            <span v-if="activeStore.currentPage === n" class="visually-hidden">(current)</span>
          </a>
        </li>
        <li v-if="index < pagesToShow.length - 1 && pagesToShow[index + 1] > n + 1" class="page-item disabled">
          <span class="page-link">...</span>
        </li>
      </template>

      <li class="page-item" :class="{ 'disabled': activeStore.currentPage === activeStore.numberOfPages }">
        <a class="page-link" href="#" @click.prevent="changePage(activeStore.currentPage + 1)" aria-label="Next">
          <span class="me-1 d-none d-sm-inline">{{t('message.seuraava')}}</span>
          <span aria-hidden="true">&raquo;</span>
        </a>
      </li>
    </ul>
  </nav>
</template>

<style scoped>
.pagination {
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.08);
  border-radius: 0.5rem;
  overflow: hidden;
}

.page-item:first-child .page-link {
  border-top-left-radius: 0.5rem;
  border-bottom-left-radius: 0.5rem;
}

.page-item:last-child .page-link {
  border-top-right-radius: 0.5rem;
  border-bottom-right-radius: 0.5rem;
}

.page-item.active .page-link {
  background-color: #4E008E !important;
  border-color: #4E008E !important;
  color: white !important;
  font-weight: 600;
  z-index: 3;
}

.page-item.disabled .page-link {
  color: #6c757d !important;
  background-color: #fff;
  border-color: #dee2e6;
  cursor: not-allowed;
}

.page-link {
  color: #4E008E !important;
  border: 1px solid #dee2e6;
  padding: 0.375rem 0.625rem;
  font-weight: 500;
  font-size: 0.9rem;
  transition: background-color 0.15s ease-in-out;
  min-width: 38px;
  text-align: center;
}

.page-link:hover:not(.disabled) {
  color: #4E008E !important;
  background-color: #f0f0f0 !important;
}

.page-link:focus {
  box-shadow: none !important;
  outline: none !important;
}

.page-link:focus-visible {
  box-shadow: none !important;
  outline: none !important;
}

/* Responsive adjustments */
@media (max-width: 576px) {
  .pagination {
    font-size: 0.8rem;
  }

  .page-link {
    padding: 0.25rem 0.4rem;
    min-width: 32px;
  }
}
</style>