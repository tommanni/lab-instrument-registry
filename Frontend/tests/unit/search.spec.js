import { mount } from "@vue/test-utils";
import { describe, it, expect, vi, beforeEach } from "vitest";
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
  beforeEach(() => {
    searchDataMock.mockClear(); // Reset mock calls
  })
  it("renders input and button correctly", () => {
    const wrapper = mount(Search, {
      props: { searchFunction: searchDataMock, cookieName: "TestCookie" },
      ...globalMock
    });
    expect(wrapper.find("input").exists()).toBe(true)
    expect(wrapper.find("button").exists()).toBe(true)
  })
  it("updates searchTerm when input changes", async () => {
    const wrapper = mount(Search, {
      props: { searchFunction: searchDataMock, cookieName: "TestCookie" },
      ...globalMock
    });
    const input = wrapper.find("input");

    await input.setValue("Vue Testing");
    expect(input.element.value).toBe("Vue Testing");
  });

  it("calls store.searchData() when button is clicked", async () => {
    const wrapper = mount(Search, {
      props: { searchFunction: searchDataMock, cookieName: "TestCookie" },
      ...globalMock
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
      ...globalMock
    });

    const input = wrapper.find("input");
    await input.setValue("Enter Pressed");
    await input.trigger("keyup.enter");

    expect(searchDataMock).toHaveBeenCalledTimes(1);
    expect(searchDataMock).toHaveBeenCalledWith("Enter Pressed");
  });
})
