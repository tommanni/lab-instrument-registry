import { describe, it, expect, vi, beforeEach } from 'vitest'
import { mount } from '@vue/test-utils'
import ChangeAdminStatus from '@/components/ChangeAdminStatus.vue'
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

// Mock translations
const i18n = createI18n({
  legacy: false,
  globalInjection: true,
  locale: 'en',
  messages: {
    en: {
      message: {
        admin_luotu: 'Admin created',
        admin_poistettu: 'Admin removed',
        virhe: 'Error: ',
        tuntematon_virhe: 'Unknown error'
      }
    }
  }
})

describe('ChangeAdminStatus.vue (Admin Rights Toggle)', () => {
  let wrapper

  const testUser = {
    id: 7,
    full_name: 'Test Person',
    email: 'test@example.com',
    is_staff: false
  }

  beforeEach(() => {
    vi.clearAllMocks()
    wrapper = mount(ChangeAdminStatus, {
      props: { user: testUser },
      global: {
        plugins: [i18n]
      }
    })
  })

  it('makes user admin when backend returns newAdminStatus = true', async () => {
    axios.post.mockResolvedValue({
      data: { newAdminStatus: true }
    })

    await wrapper.find('button').trigger('click')

    // emitted update-user event contains updated is_staff field
    expect(wrapper.emitted('update-user')).toBeTruthy()
    const updated = wrapper.emitted('update-user')[0][0]
    expect(updated.is_staff).toBe(true)

    // correct success message
    expect(mockShowAlert).toHaveBeenCalledWith(0, 'Admin created')

    // modal closes
    expect(wrapper.emitted('close')).toBeTruthy()
  })

  it('removes admin rights when backend returns newAdminStatus = false', async () => {
    axios.post.mockResolvedValue({
      data: { newAdminStatus: false }
    })

    await wrapper.find('button').trigger('click')

    const updated = wrapper.emitted('update-user')[0][0]
    expect(updated.is_staff).toBe(false)

    expect(mockShowAlert).toHaveBeenCalledWith(0, 'Admin removed')
    expect(wrapper.emitted('close')).toBeTruthy()
  })

  it('shows backend error message when API returns known error', async () => {
    axios.post.mockRejectedValue({
      response: { data: { message: 'Not allowed' } }
    })

    await wrapper.find('button').trigger('click')

    expect(mockShowAlert).toHaveBeenCalledWith(
      1,
      'Error: Not allowed'
    )

    expect(wrapper.emitted('close')).toBeTruthy()
  })

  it('shows generic error when backend does not include message', async () => {
    axios.post.mockRejectedValue({})

    await wrapper.find('button').trigger('click')

    expect(mockShowAlert).toHaveBeenCalledWith(
      1,
      'Unknown error'
    )

    expect(wrapper.emitted('close')).toBeTruthy()
  })
})