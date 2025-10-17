import { createRouter, createWebHistory } from 'vue-router'
import HomeView from '../views/HomeView.vue'

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes: [
    {
      path: '/',
      name: 'home',
      component: HomeView,
    },
    {
      path: '/admin',
      name: 'admin',
      component: () => import('../views/AdminView.vue'),
      redirect: '/admin/users',
      children: [
        {
          path: 'users',
          name: 'admin-users',
          component: () => import('../views/UsersView.vue'),
        },
        {
          path: 'data-transfer',
          name: 'admin-data-transfer',
          component: () => import('../views/DataTransferView.vue'),
        },
      ]
    },
    {
      path: '/contracts',
      name: 'contracts',
      component: () => import('../views/ContractsView.vue'),
    },
    {
      path: '/users/:id',
      name: 'UserInfoView',
      component: () => import('../views/UserInfoView.vue')
    },
  ],
})

export default router
