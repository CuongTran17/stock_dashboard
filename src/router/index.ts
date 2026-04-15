import { createRouter, createWebHistory } from 'vue-router'
import { isLoggedIn, isAdmin, isPremium } from '@/services/authApi'

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  scrollBehavior(to, from, savedPosition) {
    return savedPosition || { left: 0, top: 0 }
  },
  routes: [
    // ── Public / Market Routes ───────────────────────────────────
    {
      path: '/',
      name: 'StockDashboard',
      component: () => import('../views/StockDashboard.vue'),
      meta: { title: 'Bảng điều khiển cổ phiếu' },
    },
    {
      path: '/market-overview',
      name: 'MarketOverview',
      component: () => import('../views/MarketOverview.vue'),
      meta: { title: 'Tổng quan thị trường' },
    },
    {
      path: '/stocks/:symbol',
      name: 'StockDetail',
      component: () => import('../views/StockDetail.vue'),
      meta: { title: 'Chi tiết cổ phiếu' },
    },
    {
      path: '/screener',
      name: 'StockScreener',
      component: () => import('../views/StockScreener.vue'),
      meta: { title: 'Lọc cổ phiếu' },
    },
    {
      path: '/portfolio-alerts',
      name: 'PortfolioAlerts',
      component: () => import('../views/PortfolioAlerts.vue'),
      meta: { title: 'Danh mục và cảnh báo' },
    },
    {
      path: '/news-events',
      name: 'NewsEvents',
      component: () => import('../views/NewsEvents.vue'),
      meta: { title: 'Tin tức và sự kiện' },
    },

    // ── AI Analysis (Premium gated) ─────────────────────────────
    {
      path: '/ai-analysis',
      name: 'StockAIAnalysis',
      component: () => import('../views/StockAIAnalysis.vue'),
      meta: { title: 'Phân tích cổ phiếu bằng AI', requiresAuth: true, requiresPremium: true },
    },

    // ── Premium Upgrade ─────────────────────────────────────────
    {
      path: '/premium',
      name: 'PremiumUpgrade',
      component: () => import('../views/PremiumUpgrade.vue'),
      meta: { title: 'Nâng cấp Premium', requiresAuth: true },
    },

    // ── User Portfolio Management ───────────────────────────────
    {
      path: '/my-portfolio',
      name: 'MyPortfolio',
      component: () => import('../views/MyPortfolio.vue'),
      meta: { title: 'Danh mục của tôi', requiresAuth: true },
    },

    // ── Admin Routes ────────────────────────────────────────────
    {
      path: '/admin/sales',
      name: 'AdminSalesDashboard',
      component: () => import('../views/Admin/SalesDashboard.vue'),
      meta: { title: 'Quản trị doanh thu', requiresAuth: true, requiresAdmin: true },
    },
    {
      path: '/admin/portfolios',
      name: 'AdminCustomerPortfolios',
      component: () => import('../views/Admin/CustomerPortfolios.vue'),
      meta: { title: 'Danh mục khách hàng', requiresAuth: true, requiresAdmin: true },
    },

    // ── Auth Routes ─────────────────────────────────────────────
    {
      path: '/signin',
      name: 'Signin',
      component: () => import('../views/Auth/Signin.vue'),
      meta: { title: 'Đăng nhập' },
    },
    {
      path: '/signup',
      name: 'Signup',
      component: () => import('../views/Auth/Signup.vue'),
      meta: { title: 'Đăng ký' },
    },
    {
      path: '/welcome',
      name: 'GuestGate',
      component: () => import('../views/Auth/GuestGate.vue'),
      meta: { title: 'Join With Us' },
    },
    {
      path: '/profile',
      name: 'Profile',
      component: () => import('../views/Profile.vue'),
      meta: { title: 'Tài khoản của tôi', requiresAuth: true },
    },

    // ── Catch-all ───────────────────────────────────────────────
    {
      path: '/:pathMatch(.*)*',
      redirect: '/welcome',
      meta: { title: 'Bảng điều khiển cổ phiếu' },
    },
  ],
})

// ── Navigation Guards ─────────────────────────────────────────────
router.beforeEach((to, from, next) => {
  document.title = `${to.meta.title} | The Fin1`

  const publicPaths = ['/welcome', '/signin', '/signup']
  const isPublicRoute = publicPaths.includes(to.path)

  if (!isLoggedIn() && !isPublicRoute) {
    return next({ name: 'GuestGate' })
  }

  if (isLoggedIn() && isPublicRoute) {
    return next({ name: 'StockDashboard' })
  }

  // Auth check
  if (to.meta.requiresAuth && !isLoggedIn()) {
    return next({ name: 'Signin', query: { redirect: to.fullPath } })
  }

  // Admin check
  if (to.meta.requiresAdmin && !isAdmin()) {
    return next({ name: 'StockDashboard' })
  }

  // Premium check
  if (to.meta.requiresPremium && !isPremium()) {
    return next({ name: 'PremiumUpgrade' })
  }

  next()
})

export default router
