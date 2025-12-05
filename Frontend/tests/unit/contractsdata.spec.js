import { mount } from "@vue/test-utils";
import { describe, it, expect, vi, beforeEach } from "vitest";
import { createRouter, createMemoryHistory } from 'vue-router';
import { createI18n } from 'vue-i18n';
import { createPinia } from 'pinia';
import { nextTick } from 'vue';

// Component under test
import ContractsData from "@/components/ContractsData.vue";

const contractStoreMock = {
  data: [{
    id: 1,
    tuotenimi: 'Instrument A',
    tuotenimi_en: 'Instrument A',
    seuraava_huolto: '2025-12-01',
    edellinen_huolto: '2024-12-01',
    vastuuhenkilo: 'Jane Doe',
    huoltosopimus_loppuu: '2025-12-20'
  }],
  // pagination/sorting
  dataVisible: [],
  sortColumn: 'tuotenimi',
  sortDirection: 'none',
  currentPage: 1,
  numberOfPages: 1,
  // alert counts for header icons
  isUrgent: 0,
  isUpcoming: 0,
  isEnding: 0,
  isEnded: 0,
  // functions used by component
  updateVisibleData: vi.fn(),
  updateObject: vi.fn(),
  fetchData: vi.fn(async () => {
    // simulate async update and set visible slice
    contractStoreMock.numberOfPages = 1;
  }),
  // helper for tests: allow toggling urgency without re-mocking
  isMaintenanceDue: (d) => false,
  isMaintenanceUpcoming: (d) => false
};

// return the same mock every time useContractStore is called
vi.mock('@/stores/contract', () => ({
  useContractStore: vi.fn(() => contractStoreMock)
}));

// Mock other stores used by nested components so they won't call real Pinia
vi.mock('@/stores/alert', () => ({
  useAlertStore: vi.fn(() => ({ showAlert: vi.fn() }))
}));

vi.mock('@/stores/data', () => ({
  useDataStore: vi.fn(() => ({ isLoggedIn: true }))
}));

vi.mock('@/stores/user', () => ({
  useUserStore: vi.fn(() => ({ user: { id: 1, is_staff: true, is_superuser: false } }))
}));

const i18n = createI18n({
  legacy: false,
  globalInjection: true,
  locale: 'en',
  messages: {
    en: {
      message: {
        huoltosivu: 'Contracts',
        placeholder: 'Search...',
        haku_painike: 'Search',
        ...{} // keep flexible
      },
      contractHeaders: [
        'Product Name',
        'Next Maintenance',
        'Previous Maintenance',
        'Person in charge',
        'Contract Ends'
      ]
    }
  }
});

describe('ContractsData.vue', () => {
  const routes = [
    { path: '/', name: 'home', component: { template: '<div/>' } },
    { path: '/contracts', name: 'contracts', component: { template: '<div/>' } }
  ];

  let router, pinia;

  beforeEach(async () => {
    contractStoreMock.updateVisibleData.mockClear();
    contractStoreMock.updateObject.mockClear();
    contractStoreMock.fetchData.mockClear();
    contractStoreMock.currentPage = 1;
    contractStoreMock.numberOfPages = 1;
    contractStoreMock.isUrgent = 0;
    contractStoreMock.isUpcoming = 0;
    contractStoreMock.dataVisible = contractStoreMock.data.slice(); // ensure visible slice populated

    router = createRouter({ history: createMemoryHistory(), routes });
    pinia = createPinia();
    await router.push('/');
    await router.isReady();
  });

  it('renders headers and a single data row', async () => {
    const wrapper = mount(ContractsData, {
      global: {
        plugins: [i18n, router, pinia],
      }
    });

    await nextTick();

    // check header labels
    const headerTexts = wrapper.findAll('th .header-text').map(h => h.text());
    expect(headerTexts).toEqual([
      'Product Name',
      'Next Maintenance',
      'Previous Maintenance',
      'Person in charge',
      'Contract Ends'
    ]);

    // table row rendered
    const rows = wrapper.findAll('tbody tr');
    expect(rows.length).toBe(1);
    expect(rows[0].text()).toContain('Instrument A');
    expect(rows[0].text()).toContain('2025-12-01');
    expect(rows[0].text()).toContain('Jane Doe');
  });

  it('shows urgent/upcoming icons in headers when computed values > 0', async () => {
    // no icons initially
    contractStoreMock.isUrgent = 0;
    contractStoreMock.isUpcoming = 0;

    let wrapper = mount(ContractsData, { global: { plugins: [i18n, router, pinia] } });
    await nextTick();
    expect(wrapper.find('th .bi-exclamation-circle-fill').exists()).toBe(false);

    // set urgent for next maintenance
    contractStoreMock.isUrgent = 2;
    wrapper = mount(ContractsData, { global: { plugins: [i18n, router, pinia] } });
    await nextTick();
    const icon = wrapper.findAll('th')[1].find('i');
    expect(icon.exists()).toBe(true);
    expect(icon.classes()).toContain('bi-exclamation-circle-fill');
    expect(icon.classes()).toContain('text-danger');

    // upcoming for contract endings
    contractStoreMock.isUrgent = 0;
    contractStoreMock.isUpcoming = 0;
    contractStoreMock.isEnding = 1;
    wrapper = mount(ContractsData, { global: { plugins: [i18n, router, pinia] } });
    await nextTick();
    const endIcon = wrapper.findAll('th')[4].find('i');
    expect(endIcon.exists()).toBe(true);
    expect(endIcon.classes()).toContain('bi-exclamation-circle-fill');
  });

  it('has a resizer element on headers', async () => {
    const wrapper = mount(ContractsData, { global: { plugins: [i18n, router, pinia] } });
    await nextTick();

    const resizers = wrapper.findAll('.resizer');
    // expect a resizer per header cell (same logic as in component)
    expect(resizers.length).toBe(5);
    // first resizer exists and is visible
    expect(resizers[0].exists()).toBe(true);
  });

  it('clicking header triggers sorting and calls store.updateVisibleData', async () => {
    contractStoreMock.sortColumn = 'tuotenimi';
    contractStoreMock.sortDirection = 'asc';

    const wrapper = mount(ContractsData, { global: { plugins: [i18n, router, pinia] } });
    await nextTick();

    // click first header to toggle sorting
    const header = wrapper.findAll('th')[0].find('.sort-wrapper');
    await header.trigger('click');

    // store should be updated (component toggles sort direction and calls updateVisibleData)
    expect(contractStoreMock.sortDirection).toBe('desc');
    expect(contractStoreMock.updateVisibleData).toHaveBeenCalled();
  });
});

