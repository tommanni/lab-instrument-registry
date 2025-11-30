import { describe, it, expect, vi, beforeEach } from 'vitest'
import { mount } from '@vue/test-utils'
import { createI18n } from 'vue-i18n'
import PasswordOverlay from '@/components/PasswordOverlay.vue'
import axios from 'axios'

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

const i18n = createI18n({
	legacy: false,
	globalInjection: true,
	locale: 'en',
	messages: {
		en: {
			message: {
				vaihda_salasana: 'Change password',
				tayta_molemmat_kentat: 'Please fill both fields',
				salasanat_eivat_tasmaa: 'Passwords do not match',
				salasana_vaihdettu: 'Password changed successfully',
				virhe: 'Error: ',
				tuntematon_virhe: 'Unknown error'
			}
		}
	}
})

describe('PasswordOverlay.vue', () => {
	beforeEach(() => {
		vi.clearAllMocks()
	})

	it('opens overlay and submits password successfully', async () => {
		axios.post.mockResolvedValueOnce({ data: { success: true } })

		const wrapper = mount(PasswordOverlay, {
			props: { user: { id: 42 }, warningVisible: false },
			global: { plugins: [i18n] }
		})

		// Open overlay
		const openBtn = wrapper.find('button.btn.btn-primary')
		await openBtn.trigger('click')

		// Fill inputs
		const inputs = wrapper.findAll('input[type="password"]')
		await inputs[0].setValue('newpass1')
		await inputs[1].setValue('newpass1')

		// Submit
		const submitBtn = wrapper.find('.modal-buttons button.btn.btn-primary')
		await submitBtn.trigger('click')

		expect(axios.post).toHaveBeenCalledWith(
			'/api/change-password/',
			{ new_password: 'newpass1', id: 42 },
			{ withCredentials: true }
		)

		// Alert for success shown
		expect(mockShowAlert).toHaveBeenCalledWith(0, expect.stringContaining('Password changed successfully'))
	})

	it('shows server-side password validation error (too short)', async () => {
		// Server will respond with validation message and password_error
		axios.post.mockRejectedValueOnce({
			response: {
				data: {
					message: 'Validation failed',
					password_error: 'Password must contain at least 8 characters'
				}
			}
		})

		const wrapper = mount(PasswordOverlay, {
			props: { user: { id: 9 }, warningVisible: false },
			global: { plugins: [i18n] }
		})

		// Open overlay
		await wrapper.find('button.btn.btn-primary').trigger('click')

		// Fill inputs with a too-short password
		const inputs = wrapper.findAll('input[type="password"]')
		await inputs[0].setValue('short')
		await inputs[1].setValue('short')

		// Submit (target the submit button inside overlay)
		await wrapper.find('.modal-buttons button.btn.btn-primary').trigger('click')

		// Wait for promise microtask queue to settle
		await new Promise((resolve) => setTimeout(resolve, 0))

		// Should show general error alert
		expect(mockShowAlert).toHaveBeenCalledWith(1, expect.stringContaining('Validation failed'))

		// Inline password error should be shown in the component
		const errorText = wrapper.find('.error-text').text()
		expect(errorText).toContain('Password must contain at least 8 characters')
	})

	it('shows alert for empty or mismatched passwords', async () => {
		const wrapper = mount(PasswordOverlay, {
			props: { user: { id: 7 }, warningVisible: false },
			global: { plugins: [i18n] }
		})

		// Open overlay
		await wrapper.find('button.btn.btn-primary').trigger('click')

		// Submit with empty fields (target submit button inside overlay)
		await wrapper.find('.modal-buttons button.btn.btn-primary').trigger('click')
		expect(mockShowAlert).toHaveBeenCalledWith(1, expect.stringContaining('Please fill both fields'))
		
		// Fill only one password
		const inputs = wrapper.findAll('input[type="password"]')
		await inputs[0].setValue('a')
		await wrapper.find('.modal-buttons button.btn.btn-primary').trigger('click')
		expect(mockShowAlert).toHaveBeenCalledWith(1, expect.stringContaining('Please fill both fields'))

		// Fill mismatched passwords
		await inputs[1].setValue('b')
		await wrapper.find('.modal-buttons button.btn.btn-primary').trigger('click')
		expect(mockShowAlert).toHaveBeenCalledWith(1, expect.stringContaining('Passwords do not match'))
	})
})

