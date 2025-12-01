import { mount } from "@vue/test-utils";
import { describe, it, expect, vi, beforeEach } from "vitest";
import { createRouter, createMemoryHistory } from 'vue-router';
import { createI18n } from 'vue-i18n';
import { createPinia } from 'pinia';
import { nextTick } from 'vue';
import ContractsView from "@/views/ContractsView.vue";

// singleton mocked store so component & tests share the same object
const contractStoreMock = {
  fetchData: vi.fn(async () => Promise.resolve()),
  updateVisibleData: vi.fn(),
  currentPage: 1,
  numberOfPages: 1,
};

// Provide same mocked object for every call to useContractStore
vi.mock('@/stores/contract', () => ({
  useContractStore: vi.fn(() => contractStoreMock)
}));

// Default data store — we can override per test by re-implementing the mock
const dataStoreMock = {
  isLoggedIn: true,
};
vi.mock('@/stores/data', () => ({
  useDataStore: vi.fn(() => dataStoreMock),
}));

vi.mock('@/stores/user', () => ({
  useUserStore: vi.fn(() => ({
    user: { id: 1, is_staff: false, is_superuser: false }
  }))
}));

const i18n = createI18n({
  legacy: false,
  globalInjection: true,
  locale: 'en',
  messages: {
    en: {
      message: {
        huoltoteksti: 'Contracts',
        haku_painike: 'Search',
        haku_info_title: 'Search info',
        haku_info_content: 'Search content',
      },
      contractHeaders: ['Name', 'Next maintenance', 'Prev', 'Person', 'Ends']
    }
  }
});

// add helper
function wait(ms = 10) {
  return new Promise(resolve => setTimeout(resolve, ms));
}
async function waitForRoute(router, expectedPath, timeout = 300) {
  const start = Date.now();
  while (router.currentRoute.value.path !== expectedPath && Date.now() - start < timeout) {
    await wait(10);
  }
}

describe('ContractsView.vue', () => {
  const routes = [
    // include components or simple stub components for each path to silence Vue Router warnings
    { path: '/', name: 'home', component: { template: '<div/>' } },
    { path: '/contracts', name: 'contracts', component: { template: '<div/>' } },
  ];

  let router;
  let pinia;

  beforeEach(async () => {
    // Reset spies
    contractStoreMock.fetchData.mockClear();
    contractStoreMock.updateVisibleData.mockClear();
    contractStoreMock.currentPage = 1;
    contractStoreMock.numberOfPages = 1;

    router = createRouter({ history: createMemoryHistory(), routes });
    pinia = createPinia();

    // Provide a fetchData mock that reads router.query.page and sets currentPage
    contractStoreMock.fetchData = vi.fn(async () => {
      // small microtask to simulate async behavior
      await Promise.resolve();
      // set numberOfPages to allow page clamping logic
      contractStoreMock.numberOfPages = 5;
      const page = router.currentRoute.value.query?.page ? parseInt(router.currentRoute.value.query.page, 10) : 1;
      contractStoreMock.currentPage = Number.isNaN(page) ? 1 : page;
    });

    // push to the default route
    await router.push('/');
    await router.isReady();
  });

  it('redirects to main page (/) when not logged in', async () => {
    // set store to not logged in
    dataStoreMock.isLoggedIn = false;

    // push to contracts route and mount
    await router.push('/contracts');
    await router.isReady();

    const replaceSpy = vi.spyOn(router, 'replace');

    mount(ContractsView, {
      global: {
        plugins: [i18n, router, pinia],
      }
    });

    // Wait for onMounted and router replace to finish
    await wait(50);
    await nextTick();
    await waitForRoute(router, '/');

    expect(replaceSpy).toHaveBeenCalledWith('/');
    expect(router.currentRoute.value.path).toBe('/');
  });

  it('calls fetchData on mount and does not redirect when logged in', async () => {
    dataStoreMock.isLoggedIn = true;

    await router.push('/contracts');
    await router.isReady();

    const wrapper = mount(ContractsView, {
      global: {
        plugins: [i18n, router, pinia]
      }
    });

    // wait for fetchData and render
    await wait(50);
    await nextTick();

    expect(contractStoreMock.fetchData).toHaveBeenCalled();
    expect(router.currentRoute.value.path).toBe('/contracts');

    // Check for visible DOM elements that indicate child components rendered
    expect(wrapper.find('input.form-control').exists()).toBe(true); // Search
    expect(wrapper.find('table').exists()).toBe(true); // ContractsData renders a table
    expect(wrapper.find('ul.pagination').exists()).toBe(true); // Pagination
  });

  it('respects page query param on mount (page restore)', async () => {
    dataStoreMock.isLoggedIn = true;

    await router.push({ path: '/contracts', query: { page: '3' } });
    await router.isReady();

    mount(ContractsView, { global: { plugins: [i18n, router, pinia] } });

    // Let onMounted run
    await Promise.resolve();
    await nextTick();

    expect(contractStoreMock.currentPage).toBe(3);
    expect(router.currentRoute.value.path).toBe('/contracts');
  });
});