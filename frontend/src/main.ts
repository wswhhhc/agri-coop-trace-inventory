import { createApp } from 'vue'
import { createPinia } from 'pinia'

import App from './App.vue'
import { initializeTheme } from './composables/useTheme'
import router from './router'
import './styles/tokens.css'
import './styles/base.css'

initializeTheme()

const app = createApp(App)
app.use(createPinia())
app.use(router)
app.mount('#app')
