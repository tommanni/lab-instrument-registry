import { describe, it, expect, vi } from 'vitest'
import { mount } from '@vue/test-utils'
import UserData from '@/components/UserData.vue'
import { useUserStore } from '@/stores/user'
import { useAlertStore } from '@/stores/alert'
import { useDataStore } from '@/stores/data'
import { createI18n, useI18n } from 'vue-i18n'
import { createRouter, createWebHistory } from 'vue-router'

// Mocks
vi.mock('@/stores/user', () => ({
  useUserStore: () => ({
    currentData: [
      { id: 1, full_name: 'John Doe', email: 'john@example.com', is_superuser: true, is_active: true },
      { id: 2, full_name: 'Jane Smith', email: 'jane@example.com', is_superuser: false, is_active: true }
    ],
    user: {
      is_superuser: true
    }
  })
}))

vi.mock('@/stores/alert', () => ({
  useAlertStore: () => ({
    showAlert: vi.fn()
  })
}))

vi.mock('@/stores/data', () => ({
  useDataStore: () => ({
    isLoggedIn: true
  })
}))

const i18n = createI18n({
  legacy: false,
  globalInjection: true,
  locale: 'en',
  messages: {
    en: {
      userTableHeaders: ['Full Name', 'Email']
    }
  }
})

const router = createRouter({
  history: createWebHistory(),
  routes: [
    { path: '/', component: { template: '<div>Home</div>' } },
    { path: '/user/:id', name: 'UserInfoView', component: { template: '<div>User</div>' } }
  ]
})

describe('UserData.vue', () => {
  it('renders user table correctly', () => {
    const wrapper = mount(UserData, {
      global: {
        plugins: [i18n, router]
      }
    })
    const rows = wrapper.findAll('tbody tr')
    expect(rows.length).toBe(2)

    expect(rows[0].text()).toContain('John Doe')
    expect(rows[0].text()).toContain('john@example.com')

    expect(rows[1].text()).toContain('Jane Smith')
    expect(rows[1].text()).toContain('jane@example.com')
  })

  it('sorts data when header is clicked', async () => {
    const wrapper = mount(UserData, {
      global: {
        plugins: [i18n, router]
      }
    })

    const headers = wrapper.findAll('th')
    await headers[0].trigger('click')

    expect(wrapper.vm.sortKey).toBe('full_name')
    expect(wrapper.vm.sortOrder).toBe('asc')

    // Click again to reverse sort order
    await headers[0].trigger('click')
    expect(wrapper.vm.sortOrder).toBe('desc')
  })

  it('navigates to user detail when row is clicked', async () => {
    const wrapper = mount(UserData, {
      global: {
        plugins: [i18n, router]
      }
    })

    const pushSpy = vi.spyOn(router, 'push')
    const rows = wrapper.findAll('tbody tr')

    // Mock user data should have an id property
    await rows[0].trigger('click')

    expect(pushSpy).toHaveBeenCalled()
  })
})
