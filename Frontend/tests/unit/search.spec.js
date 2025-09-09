import { mount } from "@vue/test-utils";
import { describe, it, expect, vi } from "vitest";
import Search from "@/components/Search.vue";
import { useDataStore } from "@/stores/data";

const searchDataMock = vi.fn();
vi.mock("@/stores/data", () => ({
  useDataStore: vi.fn(() => ({
    searchData: searchDataMock,
  })),
}));
const globalMock = {
  global: {
    mocks: {
      $t: (msg) => msg,
    },
  },
};

describe("Search.vue", () => {
  it("renders input and button correctly", () => {
    const wrapper = mount(Search, globalMock);
    expect(wrapper.find("input").exists()).toBe(true)
    expect(wrapper.find("button").exists()).toBe(true)
  })
  it("updates searchTerm when input changes", async () => {
    const wrapper = mount(Search, globalMock);
    const input = wrapper.find("input");

    await input.setValue("Vue Testing");
    expect(input.element.value).toBe("Vue Testing");
  });

  it("calls store.searchData() when button is clicked", async () => {
    searchDataMock.mockClear(); // Reset mock calls
    const wrapper = mount(Search, globalMock);

    const input = wrapper.find("input");
    await input.setValue("Test Search");
    await wrapper.find("button").trigger("click");

    expect(searchDataMock).toHaveBeenCalledTimes(1);
    expect(searchDataMock).toHaveBeenCalledWith("Test Search");
  });

  it("calls store.searchData() when Enter key is pressed", async () => {
    searchDataMock.mockClear(); // Reset mock calls
    const wrapper = mount(Search, globalMock);

    const input = wrapper.find("input");
    await input.setValue("Enter Pressed");
    await input.trigger("keyup.enter");

    expect(searchDataMock).toHaveBeenCalledTimes(1);
    expect(searchDataMock).toHaveBeenCalledWith("Enter Pressed");
  });
})