import './assets/main.css'
import "bootstrap"
import 'bootstrap/dist/css/bootstrap.min.css'
import './assets/custom.scss'
import 'bootstrap-icons/font/bootstrap-icons.css';

import { createApp } from 'vue'
import { createPinia } from 'pinia'
import { createI18n } from 'vue-i18n'

import App from './App.vue'
import router from './router'

import fi from './locales/messages_fi.js'
import en from './locales/messages_en.js'

const i18n = createI18n({
    locale: 'fi',
    fallbackLocale: 'en',
    messages: {
      fi, 
	  en
    }
  });

const app = createApp(App)

app.use(createPinia())
app.use(router)
app.use(i18n)
app.mount('#app')
