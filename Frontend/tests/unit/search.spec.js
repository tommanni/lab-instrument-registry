import { mount } from "@vue/test-utils";
import { describe, it, expect, vi, beforeEach } from "vitest";
import Search from "@/components/Search.vue";
import { useDataStore } from "@/stores/data";
import { createI18n } from 'vue-i18n';

const searchDataMock = vi.fn();
vi.mock("@/stores/data", () => ({
  useDataStore: vi.fn(() => ({
    searchData: searchDataMock,
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
        nollaa_haku: 'Clear search'
      }
    }
  }
});

describe("Search.vue", () => {
  beforeEach(() => {
    searchDataMock.mockClear(); // Reset mock calls
  })
  it("renders input and button correctly", () => {
    const wrapper = mount(Search, {
      props: { searchFunction: searchDataMock, cookieName: "TestCookie" },
      global: {
        plugins: [i18n]
      }
    });
    expect(wrapper.find("input").exists()).toBe(true)
    expect(wrapper.find("button").exists()).toBe(true)
  })
  it("updates searchTerm when input changes", async () => {
    const wrapper = mount(Search, {
      props: { searchFunction: searchDataMock, cookieName: "TestCookie" },
      global: {
        plugins: [i18n]
      }
    });
    const input = wrapper.find("input");

    await input.setValue("Vue Testing");
    expect(input.element.value).toBe("Vue Testing");
  });

  it("calls store.searchData() when button is clicked", async () => {
    const wrapper = mount(Search, {
      props: { searchFunction: searchDataMock, cookieName: "TestCookie" },
      global: {
        plugins: [i18n]
      }
    });

    const input = wrapper.find("input");
    await input.setValue("Test Search");
    await wrapper.find("button").trigger("click");

    expect(searchDataMock).toHaveBeenCalledTimes(1);
    expect(searchDataMock).toHaveBeenCalledWith("Test Search");
  });

  it("calls store.searchData() when Enter key is pressed", async () => {
    const wrapper = mount(Search, {
      props: { searchFunction: searchDataMock, cookieName: "TestCookie" },
      global: {
        plugins: [i18n]
      }
    });

    const input = wrapper.find("input");
    await input.setValue("Enter Pressed");
    await input.trigger("keyup.enter");

    expect(searchDataMock).toHaveBeenCalledTimes(1);
    expect(searchDataMock).toHaveBeenCalledWith("Enter Pressed");
  });
})
