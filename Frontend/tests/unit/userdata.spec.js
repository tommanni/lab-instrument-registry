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
      { full_name: 'John Doe', email: 'john@example.com' },
      { full_name: 'Jane Smith', email: 'jane@example.com' }
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
    { path: '/user/:id', component: { template: '<div>User</div>' } }
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

  it('opens the token overlay when openTokenOverlay is called', async () => {
    const wrapper = mount(UserData, {
      global: {
        plugins: [i18n, router]
      }
    })
    await wrapper.vm.openTokenOverlay()
    expect(wrapper.vm.visible).toBe(true)
  })

  it('closes the overlay when closeOverlay is called', async () => {
    const wrapper = mount(UserData, {
      global: {
        plugins: [i18n, router]
      }
    })
    await wrapper.vm.openTokenOverlay()
    expect(wrapper.vm.visible).toBe(true)

    await wrapper.vm.closeOverlay()
    expect(wrapper.vm.visible).toBe(false)
  })
})
