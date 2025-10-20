import { mount } from "@vue/test-utils";
import { describe, it, expect, vi, beforeEach } from "vitest";
import Search from "@/components/Search.vue";
import { createI18n } from 'vue-i18n';
import { createPinia } from 'pinia';

const searchDataMock = vi.fn();

vi.mock("@/stores/data", () => ({
  useDataStore: vi.fn(() => ({
    searchData: searchDataMock,
  })),
}));

vi.mock("@/stores/user", () => ({
  useUserStore: vi.fn(() => ({
    isLoggedIn: false,
  })),
}));

const i18n = createI18n({
  legacy: false,
  globalInjection: true,
  locale: 'en',
  messages: {
    en: {
      message: {
        placeholder: 'Search...',
        haku_painike: 'Search',
        nollaa_haku: 'Clear search',
        haku_ohje: 'Search help text',
        haku_info_title: 'Search Info',
        haku_info_content: 'Search help content'
      }
    }
  }
});

describe("Search.vue", () => {
  let pinia;

  beforeEach(() => {
    searchDataMock.mockClear(); // Reset mock calls
    pinia = createPinia();
  })

  it("renders input and button correctly", () => {
    const wrapper = mount(Search, {
      props: { searchFunction: searchDataMock, searchType: "device" },
      global: {
        plugins: [i18n, pinia]
      }
    });
    expect(wrapper.find("input.form-control").exists()).toBe(true)
    expect(wrapper.find("button.btn-primary").exists()).toBe(true)
  })

  it("updates searchTerm when input changes", async () => {
    const wrapper = mount(Search, {
      props: { searchFunction: searchDataMock, searchType: "device" },
      global: {
        plugins: [i18n, pinia]
      }
    });
    const input = wrapper.find("input.form-control");

    await input.setValue("Vue Testing");
    expect(input.element.value).toBe("Vue Testing");
  });

  it("calls searchFunction when button is clicked", async () => {
    const wrapper = mount(Search, {
      props: { searchFunction: searchDataMock, searchType: "device" },
      global: {
        plugins: [i18n, pinia]
      }
    });

    await wrapper.find("button.btn-primary").trigger("click");

    expect(searchDataMock).toHaveBeenCalledTimes(1);
    expect(searchDataMock).toHaveBeenCalledWith(false);
  });

  it("calls searchFunction when Enter key is pressed", async () => {
    const wrapper = mount(Search, {
      props: { searchFunction: searchDataMock, searchType: "device" },
      global: {
        plugins: [i18n, pinia]
      }
    });

    const input = wrapper.find("input.form-control");
    await input.trigger("keyup.enter");

    expect(searchDataMock).toHaveBeenCalledTimes(1);
    expect(searchDataMock).toHaveBeenCalledWith(false);
  });
})
