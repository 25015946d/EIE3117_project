import { createStore } from 'vuex'
import axios from 'axios'

axios.defaults.baseURL = process.env.VUE_APP_API_BASE_URL || ''

const TOKEN_KEY = 'auth_token'
const USER_KEY = 'current_user'

function loadJson(key, fallback) {
  try {
    const raw = localStorage.getItem(key)
    return raw ? JSON.parse(raw) : fallback
  } catch (e) {
    return fallback
  }
}

function saveJson(key, value) {
  try {
    localStorage.setItem(key, JSON.stringify(value))
  } catch (e) {}
}

const store = createStore({
  state: {
    token: localStorage.getItem(TOKEN_KEY) || null,
    currentUser: loadJson(USER_KEY, null)
  },
  getters: {
    isAuthenticated(state) {
      return !!state.token
    },
    currentUser(state) {
      return state.currentUser
    }
  },
  mutations: {
    setAuth(state, { token, user }) {
      state.token = token
      state.currentUser = user
      if (token) localStorage.setItem(TOKEN_KEY, token)
      if (user) saveJson(USER_KEY, user)
    },
    clearAuth(state) {
      state.token = null
      state.currentUser = null
      localStorage.removeItem(TOKEN_KEY)
      localStorage.removeItem(USER_KEY)
    },
    setCurrentUser(state, user) {
      state.currentUser = user
      saveJson(USER_KEY, user)
    }
  },
  actions: {
    async login({ commit }, payload) {
      const res = await axios.post('/auth/login/', payload)
      const token = res.data?.token || res.data?.access || res.data?.key || null
      const user = res.data?.user || res.data?.profile || null
      commit('setAuth', { token, user })
      return res.data
    },
    async register({ commit }, formData) {
      const res = await axios.post('/auth/register/', formData)
      const token = res.data?.token || res.data?.access || res.data?.key || null
      const user = res.data?.user || res.data?.profile || null
      if (token || user) commit('setAuth', { token, user })
      return res.data
    },
    async updateProfile({ commit }, formData) {
      const res = await axios.patch('/auth/profile/', formData)
      const user = res.data?.user || res.data
      commit('setCurrentUser', user)
      return res.data
    },
    logout({ commit }) {
      commit('clearAuth')
    }
  }
})

axios.interceptors.request.use((config) => {
  const token = store.state.token
  if (token) {
    config.headers = config.headers || {}
    if (!config.headers.Authorization) config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

axios.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response && error.response.data) {
      return Promise.reject(error.response.data)
    }
    return Promise.reject(error)
  }
)

export default store
