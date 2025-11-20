import { describe, it, expect, vi, beforeEach } from 'vitest'
import { mount } from '@vue/test-utils'
import { createPinia, setActivePinia } from 'pinia'
import { useDataStore } from '@/stores/data'
import LoginOverlay from '@/components/LoginOverlay.vue'
import axios from 'axios'

// Mock i18n
vi.mock('vue-i18n', () => ({
	useI18n: () => ({ t: (k) => k })
}))

// Mock router used by Pinia stores
const replaceMock = vi.fn(() => Promise.resolve())
vi.mock('vue-router', () => ({
	useRoute: () => ({ query: {}, path: '/' }),
	useRouter: () => ({ replace: replaceMock })
}))

// Dynamic mocks we control per test
let fetchDataMock
let showAlertMock

// Mock stores used inside the component
vi.mock('@/stores/contract', () => ({
	useContractStore: () => ({ fetchData: fetchDataMock })
}))
vi.mock('@/stores/alert.js', () => ({
	useAlertStore: () => ({ showAlert: showAlertMock })
}))

// Mock axios
vi.mock('axios', () => ({
	default: {
		post: vi.fn()
	}
}))

describe('LoginOverlay.vue', () => {
	let pinia

	beforeEach(() => {
		setActivePinia(pinia = createPinia())
		fetchDataMock = vi.fn().mockResolvedValue(undefined)
		showAlertMock = vi.fn()
		axios.post.mockReset()
	})

	it('logs in successfully: sets store, closes overlay, calls fetchData and shows success alert', async () => {
		const wrapper = mount(LoginOverlay, {
			global: {
				plugins: [pinia]
			}
		})

		const store = useDataStore()
		expect(store.isLoggedIn).toBe(false)

		// Open overlay
		await wrapper.find('button').trigger('click')
		expect(wrapper.find('.overlay-backdrop').exists()).toBe(true)

		// Fill and submit
		await wrapper.find('#login-email').setValue('a@a.com')
		await wrapper.find('#login-password').setValue('secret123')

		const userPayload = { id: 1, email: 'a@a.com', full_name: 'Test User' }
		axios.post.mockResolvedValueOnce({ data: { user: userPayload } })

		await wrapper.find('form').trigger('submit.prevent')
		// allow promises to resolve
		await Promise.resolve()
		await Promise.resolve()

		// Correct axios call with credentials
		expect(axios.post).toHaveBeenCalledWith('/api/login/', {
			email: 'a@a.com',
			password: 'secret123'
		}, { withCredentials: true })

		// Store updated
		expect(store.isLoggedIn).toBe(true)
		expect(store.user).toEqual(userPayload)

		// Overlay closed
		expect(wrapper.find('.overlay-backdrop').exists()).toBe(false)

		// Contract data fetched
		expect(fetchDataMock).toHaveBeenCalledTimes(1)

		// Success alert shown
		expect(showAlertMock).toHaveBeenCalledWith(0, 'message.sisaan_kirjauduttu')
	})

	it('shows error alert and keeps overlay open when login fails', async () => {
		const wrapper = mount(LoginOverlay, {
			global: {
				plugins: [createPinia()]
			}
		})

		const store = useDataStore()

		// Open overlay
		await wrapper.find('button').trigger('click')
		expect(wrapper.find('.overlay-backdrop').exists()).toBe(true)

		// Fill and submit
		await wrapper.find('#login-email').setValue('a@a.com')
		await wrapper.find('#login-password').setValue('wrong')

		axios.post.mockRejectedValueOnce({ response: { status: 401 } })

		await wrapper.find('form').trigger('submit.prevent')
		await Promise.resolve()
		await Promise.resolve()

		// Store not logged in
		expect(store.isLoggedIn).toBe(false)

		// Overlay still open
		expect(wrapper.find('.overlay-backdrop').exists()).toBe(true)

		// Error alert shown
		expect(showAlertMock).toHaveBeenCalledWith(1, 'message.kirjautumisvirhe')
	})
})


