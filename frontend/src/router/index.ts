import { createRouter, createWebHistory } from 'vue-router'
import HomeView from '../views/HomeView.vue'

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes: [
    {
      path: '/',
      name: 'home',
      component: HomeView,
      meta: { title: 'Home - T2 LLM Platform' }
    },
    {
      path: '/dashboard',
      name: 'dashboard',
      component: () => import('../views/DashboardView.vue'),
      meta: { title: 'Dashboard - T2 LLM Platform' }
    },
    {
      path: '/optimize',
      name: 'optimize',
      component: () => import('../views/OptimizeView.vue'),
      meta: { title: 'Optimize - T2 LLM Platform' }
    },
    {
      path: '/analytics',
      name: 'analytics',
      component: () => import('../views/AnalyticsView.vue'),
      meta: { title: 'Analytics - T2 LLM Platform' }
    },
    {
      path: '/schedule',
      name: 'schedule',
      component: () => import('../views/ScheduleView.vue'),
      meta: { title: 'Расписание - T2 Platform' }
    },
    {
      path: '/reps',
      name: 'reps',
      component: () => import('../views/RepsView.vue'),
      meta: { title: 'Сотрудники - T2 Platform' }
    },
    // Redirect to home if route not found
    {
      path: '/:pathMatch(.*)*',
      redirect: '/'
    }
  ]
})

// Update document title on route change
router.beforeEach((to, _from, next) => {
  document.title = (to.meta.title as string) || 'T2 LLM Platform'
  next()
})

export default router
