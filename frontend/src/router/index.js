import { createRouter, createWebHistory } from 'vue-router'

import Login from '../views/Login.vue'
import Register from '../views/Register.vue'
import Profile from '../views/Profile.vue'
import MyNotices from '../views/MyNotices.vue'
import AllNotices from '../views/AllNotices.vue'
import CreateNotice from '../views/CreateNotice.vue'
import NoticeDetail from '../views/NoticeDetail.vue'

const routes = [
  { path: '/', name: 'home', component: AllNotices },
  { path: '/login', name: 'login', component: Login },
  { path: '/register', name: 'register', component: Register },
  { path: '/profile', name: 'profile', component: Profile },
  { path: '/my-notices', name: 'my-notices', component: MyNotices },
  { path: '/all-notices', name: 'all-notices', component: AllNotices },
  { path: '/create', name: 'create', component: CreateNotice },
  { path: '/notice/:id', name: 'notice-detail', component: NoticeDetail, props: true }
]

const router = createRouter({
  history: createWebHistory(process.env.BASE_URL),
  routes
})

export default router
