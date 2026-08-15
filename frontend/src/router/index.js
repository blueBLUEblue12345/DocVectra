import { createRouter, createWebHistory } from 'vue-router'
import ChatView from '../views/ChatView.vue'
import ImportView from '../views/ImportView.vue'

const routes = [
  {
    path: '/',
    redirect: '/chat'
  },
  {
    path: '/chat',
    name: 'Chat',
    component: ChatView
  },
  {
    path: '/import',
    name: 'Import',
    component: ImportView
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

export default router
