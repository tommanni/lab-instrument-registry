import { describe, it, expect, vi, beforeEach } from 'vitest'
import { mount, flushPromises } from '@vue/test-utils'
import UserInfoView from '@/views/UserInfoView.vue'
import ConfirmationOverlay from '@/components/ConfirmationOverlay.vue'
import ChangeAdminStatus from '@/components/ChangeAdminStatus.vue'
import ChangeSuperadminStatus from '@/components/ChangeSuperadminStatus.vue'
import DeleteUser from '@/components/DeleteUser.vue'
import axios from 'axios'
import { createRouter, createMemoryHistory } from 'vue-router'
import { createPinia } from 'pinia'
import { createI18n } from 'vue-i18n'


// Mock axios
vi.mock('axios', () => ({
  default: {
    get: vi.fn(),
    post: vi.fn()
  }
}))

// Mock stores
const mockShowAlert = vi.fn()
vi.mock('@/stores/alert', () => ({
  useAlertStore: () => ({
    showAlert: mockShowAlert
  })
}))
vi.mock('@/stores/data', () => ({
  useDataStore: () => ({ 
    isLoggedIn: true,
    user: { id: 1, is_staff: true, is_superuser: true }
  })
}))
vi.mock('@/stores/user', () => ({
  useUserStore: () => ({ 
    user: { id: 1, is_staff: true, is_superuser: true },
    fetchUser: vi.fn().mockResolvedValue()
  })
}))

// Setup router
const router = createRouter({
  history: createMemoryHistory(),
  routes: [
    { path: '/users/:id', component: UserInfoView },
    { path: '/', component: { template: '<div>Home</div>' } }
  ]
})

const pinia = createPinia()

const i18n = createI18n({
  legacy: false,
  globalInjection: true,
  locale: 'en',
  messages: {}
})

describe('UserInfoView.vue - simplified overlay tests', () => {
  let wrapper
  const targetUser = { id: 5, is_staff: false, is_superuser: false }

  beforeEach(async () => {
    vi.clearAllMocks()
    axios.get.mockResolvedValue({ data: targetUser })

    await router.push('/users/5')
    await router.isReady()

    wrapper = mount(UserInfoView, {
        global: {
            plugins: [router, pinia, i18n],
        stubs: { UserInfo: true, PasswordOverlay: true }
    },
    attachTo: document.body
})

    await flushPromises()
  })

  it('opens admin overlay with correct component', async () => {
    // Find first primary button in action-buttons-container (make admin button for regular users)
    const buttons = wrapper.findAll('.action-buttons-container button.btn-primary')
    await buttons[0].trigger('click')

    const overlay = wrapper.findComponent(ConfirmationOverlay)
    expect(overlay.exists()).toBe(true)
    expect(overlay.props('component')).toBe(ChangeAdminStatus)
    expect(overlay.props('user').id).toBe(targetUser.id)
  })

  it('opens superadmin overlay with correct component', async () => {
    // Find second primary button in action-buttons-container (make superadmin button)
    const buttons = wrapper.findAll('.action-buttons-container button.btn-primary')
    await buttons[1].trigger('click')

    const overlay = wrapper.findComponent(ConfirmationOverlay)
    expect(overlay.exists()).toBe(true)
    expect(overlay.props('component')).toBe(ChangeSuperadminStatus)
    expect(overlay.props('user').id).toBe(targetUser.id)
  })

  it('opens delete overlay with correct component', async () => {
    // Find danger button (delete button)
    const deleteBtn = wrapper.find('.action-buttons-container button.btn-danger')
    await deleteBtn.trigger('click')

    const overlay = wrapper.findComponent(ConfirmationOverlay)
    expect(overlay.exists()).toBe(true)
    expect(overlay.props('component')).toBe(DeleteUser)
    expect(overlay.props('user').id).toBe(targetUser.id)
  })

  it('closes overlay when close event emitted', async () => {
    // Open overlay by clicking first button
    const buttons = wrapper.findAll('.action-buttons-container button.btn-primary')
    await buttons[0].trigger('click')

    const overlay = wrapper.findComponent(ConfirmationOverlay)
    expect(overlay.exists()).toBe(true)

    await overlay.vm.$emit('close')
    await flushPromises()

    expect(wrapper.findComponent(ConfirmationOverlay).exists()).toBe(false)
  })

  it('updates user when update-user event emitted', async () => {
    // Open overlay by clicking first button
    const buttons = wrapper.findAll('.action-buttons-container button.btn-primary')
    await buttons[0].trigger('click')

    const overlay = wrapper.findComponent(ConfirmationOverlay)
    const updatedUser = { ...targetUser, is_staff: true }

    await overlay.vm.$emit('update-user', updatedUser)
    await flushPromises()

    expect(wrapper.vm.user.is_staff).toBe(true)
  })
})