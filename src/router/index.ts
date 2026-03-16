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
        title: 'Bảng điều khiển cổ phiếu',
      },
    },
    {
      path: '/market-overview',
      name: 'MarketOverview',
      component: () => import('../views/MarketOverview.vue'),
      meta: {
        title: 'Tổng quan thị trường',
      },
    },
    {
      path: '/stocks/:symbol',
      name: 'StockDetail',
      component: () => import('../views/StockDetail.vue'),
      meta: {
        title: 'Chi tiết cổ phiếu',
      },
    },
    {
      path: '/screener',
      name: 'StockScreener',
      component: () => import('../views/StockScreener.vue'),
      meta: {
        title: 'Lọc cổ phiếu',
      },
    },
    {
      path: '/portfolio-alerts',
      name: 'PortfolioAlerts',
      component: () => import('../views/PortfolioAlerts.vue'),
      meta: {
        title: 'Danh mục và cảnh báo',
      },
    },
    {
      path: '/news-events',
      name: 'NewsEvents',
      component: () => import('../views/NewsEvents.vue'),
      meta: {
        title: 'Tin tức và sự kiện',
      },
    },
    {
      path: '/signin',
      name: 'Signin',
      component: () => import('../views/Auth/Signin.vue'),
      meta: {
        title: 'Đăng nhập',
      },
    },
    {
      path: '/signup',
      name: 'Signup',
      component: () => import('../views/Auth/Signup.vue'),
      meta: {
        title: 'Đăng ký',
      },
    },
    {
      path: '/:pathMatch(.*)*',
      redirect: '/',
      meta: {
        title: 'Bảng điều khiển cổ phiếu',
      },
    },
  ],
})

export default router

router.beforeEach((to, from, next) => {
  document.title = `${to.meta.title} | The Fin1`
  next()
})
