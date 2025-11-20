import { describe, it, expect, vi, beforeEach } from 'vitest'
import { mount } from '@vue/test-utils'
import { createI18n } from 'vue-i18n'
import RegisterOverlay from '@/components/RegisterOverlay.vue'
import axios from 'axios'

// Mocks
const mockShowAlert = vi.fn()

vi.mock('axios', () => ({
  default: {
    post: vi.fn()
  }
}))

vi.mock('@/stores/data', () => ({
  useDataStore: () => ({
    isLoggedIn: false
  })
}))

vi.mock('@/stores/alert', () => ({
  useAlertStore: () => ({
    showAlert: mockShowAlert
  })
}))

const i18n = createI18n({
  legacy: false,
  globalInjection: true,
  locale: 'en',
  messages: {
    en: {
      message: {
        register_painike: 'Register',
        rekisteroity: 'Successfully registered. You can now sign in.',
        rekisteroimisvirhe: 'Error while registering.',
        virhe: 'Error: ',
        koodi: 'Invite code',
        sahkoposti: 'Email address',
        koko_nimi: 'Full name',
        salasana: 'Password'
      }
    }
  }
})

describe('RegisterOverlay.vue', () => {
  let wrapper

  beforeEach(() => {
    vi.clearAllMocks()
    wrapper = mount(RegisterOverlay, {
      global: {
        plugins: [i18n]
      }
    })
  })

  it('renders the register button when logged out', () => {
    const button = wrapper.find('button.btn.btn-primary.ms-2')
    expect(button.exists()).toBe(true)
    expect(button.text()).toBe('Register')
  })

  it('opens overlay when the register button is clicked', async () => {
    const button = wrapper.find('button.btn.btn-primary.ms-2')
    await button.trigger('click')
    expect(wrapper.find('.overlay-backdrop').exists()).toBe(true)
  })

  it('submits successfully and closes overlay', async () => {
    axios.post.mockResolvedValueOnce({ data: {} })

    // open overlay
    await wrapper.find('button.btn.btn-primary.ms-2').trigger('click')
    expect(wrapper.find('.overlay-backdrop').exists()).toBe(true)

    // fill form
    await wrapper.find('#form3Example2').setValue('INV12345') // invite_code
    await wrapper.find('#form3Example1').setValue('user@example.com') // email
    await wrapper.find('#form3Example3').setValue('Test User') // full_name
    await wrapper.find('#form3Example4').setValue('ValidPassword123') // password
    await wrapper.find('#form3Example5').setValue('ValidPassword123') // password_again

    // submit
    await wrapper.find('form').trigger('submit.prevent')

    expect(axios.post).toHaveBeenCalledWith('/api/register/', {
      email: 'user@example.com',
      password: 'ValidPassword123',
      password_again: 'ValidPassword123',
      invite_code: 'INV12345',
      full_name: 'Test User'
    }, { withCredentials: true })

    expect(mockShowAlert).toHaveBeenCalledWith(0, 'Successfully registered. You can now sign in.')
    // overlay should close
    expect(wrapper.find('.overlay-backdrop').exists()).toBe(false)
  })

  it('shows API error and password error on failure response', async () => {
    axios.post.mockRejectedValueOnce({
      response: {
        data: {
          message: 'invite code is invalid or missing.',
          password_error: 'Passwords do not match'
        }
      }
    })

    await wrapper.find('button.btn.btn-primary.ms-2').trigger('click')
    await wrapper.find('#form3Example2').setValue('INV12345')
    await wrapper.find('#form3Example1').setValue('user@example.com')
    await wrapper.find('#form3Example3').setValue('Test User')
    await wrapper.find('#form3Example4').setValue('abc')
    await wrapper.find('#form3Example5').setValue('xyz')

    await wrapper.find('form').trigger('submit.prevent')

    expect(mockShowAlert).toHaveBeenCalledWith(1, 'Error: invite code is invalid or missing.')
    // password_error text rendered
    const errText = wrapper.find('.error-text').text()
    expect(errText).toContain('Passwords do not match')
  })

  it('shows generic error if no response from server', async () => {
    axios.post.mockRejectedValueOnce(new Error('network'))

    await wrapper.find('button.btn.btn-primary.ms-2').trigger('click')
    await wrapper.find('#form3Example2').setValue('INV12345')
    await wrapper.find('#form3Example1').setValue('user@example.com')
    await wrapper.find('#form3Example3').setValue('Test User')
    await wrapper.find('#form3Example4').setValue('ValidPassword123')
    await wrapper.find('#form3Example5').setValue('ValidPassword123')

    await wrapper.find('form').trigger('submit.prevent')

    expect(mockShowAlert).toHaveBeenCalledWith(1, 'Error while registering.')
  })
})



describe('RegisterOverlay.vue validators', () => {
  let wrapper
  const getErrorText = () => wrapper.find('.error-text').text().trim()

  beforeEach(() => {
    vi.clearAllMocks()
    wrapper = mount(RegisterOverlay, {
      global: {
        plugins: [i18n]
      }
    })
  })

  const openAndFillCommon = async ({
    invite = 'INV12345',
    email = 'user@example.com',
    fullName = 'Test User',
    pass = 'ValidPassword123',
    passAgain = 'ValidPassword123'
  } = {}) => {
    await wrapper.find('button.btn.btn-primary.ms-2').trigger('click')
    await wrapper.find('#form3Example2').setValue(invite)
    await wrapper.find('#form3Example1').setValue(email)
    await wrapper.find('#form3Example3').setValue(fullName)
    await wrapper.find('#form3Example4').setValue(pass)
    await wrapper.find('#form3Example5').setValue(passAgain)
  }

  it('success flow closes overlay and shows success', async () => {
    axios.post.mockResolvedValueOnce({ data: {} })
    await openAndFillCommon()
    await wrapper.find('form').trigger('submit.prevent')
    expect(axios.post).toHaveBeenCalled()
    expect(mockShowAlert).toHaveBeenCalledWith(0, 'Successfully registered. You can now sign in.')
    expect(wrapper.find('.overlay-backdrop').exists()).toBe(false)
  })

  it('password mismatch shows error and message', async () => {
    axios.post.mockRejectedValueOnce({
      response: {
        data: { message: 'Error validating password.', password_error: 'Passwords do not match' }
      }
    })
    await openAndFillCommon({ pass: 'abc', passAgain: 'xyz' })
    await wrapper.find('form').trigger('submit.prevent')
    expect(mockShowAlert).toHaveBeenCalledWith(1, 'Error: Error validating password.')
    expect(wrapper.find('.error-text').text()).toContain('Passwords do not match')
  })

  it('too short password shows translated message', async () => {
    axios.post.mockRejectedValueOnce({
      response: {
        data: { message: 'Error validating password.', password_error: 'Password must contain at least 8 characters' }
      }
    })
    await openAndFillCommon({ pass: 'short', passAgain: 'short' })
    await wrapper.find('form').trigger('submit.prevent')
    expect(mockShowAlert).toHaveBeenCalledWith(1, 'Error: Error validating password.')
    expect(wrapper.find('.error-text').text()).toContain('Password must contain at least 8 characters')
  })

  it('entirely numeric password shows translated message', async () => {
    axios.post.mockRejectedValueOnce({
      response: {
        data: { message: 'Error validating password.', password_error: 'Password cannot be entirely numeric' }
      }
    })
    await openAndFillCommon({ pass: '12345678', passAgain: '12345678' })
    await wrapper.find('form').trigger('submit.prevent')
    expect(mockShowAlert).toHaveBeenCalledWith(1, 'Error: Error validating password.')
    expect(wrapper.find('.error-text').text()).toContain('Password cannot be entirely numeric')
  })

  it('too common password shows translated message', async () => {
    axios.post.mockRejectedValueOnce({
      response: {
        data: { message: 'Error validating password.', password_error: 'Password is too common' }
      }
    })
    await openAndFillCommon({ pass: 'password', passAgain: 'password' })
    await wrapper.find('form').trigger('submit.prevent')
    expect(mockShowAlert).toHaveBeenCalledWith(1, 'Error: Error validating password.')
    expect(wrapper.find('.error-text').text()).toContain('Password is too common')
  })

  it('too similar to email shows translated message', async () => {
    axios.post.mockRejectedValueOnce({
      response: {
        data: { message: 'Error validating password.', password_error: 'Password is too similar to the username' }
      }
    })
    await openAndFillCommon({
      email: 'johnsmith@example.com',
      pass: 'johnsmith',
      passAgain: 'johnsmith'
    })
    await wrapper.find('form').trigger('submit.prevent')
    expect(mockShowAlert).toHaveBeenCalledWith(1, 'Error: Error validating password.')
    expect(wrapper.find('.error-text').text()).toContain('Password is too similar to the username')
  })

  it('invalid invite code shows API error without password_error', async () => {
    axios.post.mockRejectedValueOnce({
      response: {
        data: { message: 'invite code is invalid or missing.' }
      }
    })
    await openAndFillCommon()
    await wrapper.find('form').trigger('submit.prevent')
    expect(mockShowAlert).toHaveBeenCalledWith(1, 'Error: invite code is invalid or missing.')
    expect(getErrorText()).toBe('')
  })
})
