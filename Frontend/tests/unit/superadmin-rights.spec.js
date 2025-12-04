import { describe, it, expect, vi, beforeEach } from 'vitest'
import { mount } from '@vue/test-utils'
import ChangeSuperadminStatus from '@/components/ChangeSuperadminStatus.vue'
import axios from 'axios'
import { createI18n } from 'vue-i18n'

// Mock axios
vi.mock('axios', () => ({
  default: {
    post: vi.fn()
  }
}))

// Mock alert store
const mockShowAlert = vi.fn()
vi.mock('@/stores/alert', () => ({
  useAlertStore: () => ({
    showAlert: mockShowAlert
  })
}))

// Mock i18n
const i18n = createI18n({
  legacy: false,
  globalInjection: true,
  locale: 'en',
  messages: {
    en: {
      message: {
        superadmin_luotu: 'Superadmin created',
        admin_poistettu: 'Admin rights removed',
        virhe: 'Error: ',
        tuntematon_virhe: 'Unknown error',
        tee_superadmin: 'Make Superadmin',
        poista_oikeudet: 'Remove Rights'
      }
    }
  }
})

describe('ChangeSuperadminStatus.vue', () => {
  let wrapper

  const testUser = {
    id: 5,
    full_name: 'Super Tester',
    email: 'super@test.com',
    is_staff: true,
    is_superuser: false
  }

  beforeEach(() => {
    vi.clearAllMocks()
    wrapper = mount(ChangeSuperadminStatus, {
      props: { user: testUser },
      global: {
        plugins: [i18n]
      }
    })
  })

  it('grants superadmin rights when API returns newSuperadminStatus = true', async () => {
    axios.post.mockResolvedValue({
      data: { newSuperadminStatus: true }
    })

    await wrapper.find('button').trigger('click')

    // check the event emitted
    const updated = wrapper.emitted('update-user')[0][0]
    expect(updated.is_superuser).toBe(true)

    // maintain existing admin rights
    expect(updated.is_staff).toBe(testUser.is_staff)

    // correct success message
    expect(mockShowAlert).toHaveBeenCalledWith(0, 'Superadmin created')

    // always close confirmation overlay
    expect(wrapper.emitted('close')).toBeTruthy()
  })

  it('removes superadmin rights AND admin rights', async () => {
    const testUser2 = {
      ...testUser,
      is_superuser: true,
      is_staff: true
    }

    wrapper.setProps({ user: testUser2 })

    axios.post.mockResolvedValue({
      data: { newSuperadminStatus: false }
    })

    await wrapper.find('button').trigger('click')

    const updated = wrapper.emitted('update-user')[0][0]

    expect(updated.is_superuser).toBe(false)

    // special component logic: removing superadmin removes ALL admin rights
    expect(updated.is_staff).toBe(false)

    // test correct alert message
    expect(mockShowAlert).toHaveBeenCalledWith(0, 'Admin rights removed')

    expect(wrapper.emitted('close')).toBeTruthy()
  })

  it('shows backend error message when API returns error with message', async () => {
    axios.post.mockRejectedValue({
      response: { data: { message: 'Forbidden' } }
    })

    await wrapper.find('button').trigger('click')

    expect(mockShowAlert).toHaveBeenCalledWith(
      1,
      'Error: Forbidden'
    )

    expect(wrapper.emitted('close')).toBeTruthy()
  })

  it('shows generic unknown error if no backend message included', async () => {
    axios.post.mockRejectedValue({})

    await wrapper.find('button').trigger('click')

    expect(mockShowAlert).toHaveBeenCalledWith(
      1,
      'Unknown error'
    )

    expect(wrapper.emitted('close')).toBeTruthy()
  })

  it('renders correct button text depending on superadmin state', async () => {
    // Not superadmin
    expect(wrapper.find('button').text()).toBe('Make Superadmin')

    // Set as superadmin
    wrapper.setProps({
      user: { ...testUser, is_superuser: true }
    })

    await wrapper.vm.$nextTick()

    expect(wrapper.find('button').text()).toBe('Remove Rights')
  })
})