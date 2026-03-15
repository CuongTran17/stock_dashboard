import { createRouter, createWebHistory } from 'vue-router'

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  scrollBehavior(to, from, savedPosition) {
    return savedPosition || { left: 0, top: 0 }
  },
  routes: [
    {
      path: '/',
      name: 'StockDashboard',
      component: () => import('../views/StockDashboard.vue'),
      meta: {
        title: 'Stock Dashboard',
      },
    },
    {
      path: '/market-overview',
      name: 'MarketOverview',
      component: () => import('../views/MarketOverview.vue'),
      meta: {
        title: 'Market Overview',
      },
    },
    {
      path: '/stocks/:symbol',
      name: 'StockDetail',
      component: () => import('../views/StockDetail.vue'),
      meta: {
        title: 'Stock Detail',
      },
    },
    {
      path: '/screener',
      name: 'StockScreener',
      component: () => import('../views/StockScreener.vue'),
      meta: {
        title: 'Stock Screener',
      },
    },
    {
      path: '/portfolio-alerts',
      name: 'PortfolioAlerts',
      component: () => import('../views/PortfolioAlerts.vue'),
      meta: {
        title: 'Portfolio & Alerts',
      },
    },
    {
      path: '/news-events',
      name: 'NewsEvents',
      component: () => import('../views/NewsEvents.vue'),
      meta: {
        title: 'News & Events',
      },
    },
    {
      path: '/signin',
      name: 'Signin',
      component: () => import('../views/Auth/Signin.vue'),
      meta: {
        title: 'Signin',
      },
    },
    {
      path: '/signup',
      name: 'Signup',
      component: () => import('../views/Auth/Signup.vue'),
      meta: {
        title: 'Signup',
      },
    },
    {
      path: '/:pathMatch(.*)*',
      redirect: '/',
      meta: {
        title: 'Stock Dashboard',
      },
    },
  ],
})

export default router

router.beforeEach((to, from, next) => {
  document.title = `${to.meta.title} | VN Stock Workstation`
  next()
})
