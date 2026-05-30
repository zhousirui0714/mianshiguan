/**
 * 侧边栏组件 — 交互逻辑
 * 依赖：sidebar.css（样式）
 * 使用：在模板中加载本脚本后，侧边栏自动获得导航和折叠能力
 */

(function () {
    'use strict';

    /* ---- 菜单项配置 ---- */
    const SIDEBAR_MENU_ITEMS = [
        { id: 'home',     label: '首页',       icon: '🏠', url: '/' },
        { id: 'questions',label: '题库中心',   icon: '📚', url: '/question-bank' },
        { id: 'learning', label: '学习计划',   icon: '📅', url: '/learning-plan' },
        { id: 'growth',   label: '成长中心',   icon: '📈', url: '/growth' },
        { id: 'mock',     label: '模拟练习',   icon: '✍️', url: '/mock-exam' },
        { id: 'badges',   label: '成就徽章',   icon: '🏆', url: '/badges' }
    ];

    /* ---- 导航函数 ---- */
    window.sidebarNavigate = function (url) {
        window.location.href = url;
    };

    /* ---- 菜单项点击高亮 ---- */
    function initSidebarHighlight() {
        var sidebar = document.getElementById('app-sidebar');
        if (!sidebar) return;

        var currentPath = window.location.pathname;
        var navItems = sidebar.querySelectorAll('.nav-item[data-nav-id]');

        navItems.forEach(function (item) {
            item.classList.remove('active');
            var url = item.getAttribute('href');
            if (url === currentPath) {
                item.classList.add('active');
            }
        });

        // 点击高亮
        navItems.forEach(function (item) {
            item.addEventListener('click', function () {
                navItems.forEach(function (n) { n.classList.remove('active'); });
                item.classList.add('active');
            });
        });
    }

    /* ---- 折叠/展开（移动端可选） ---- */
    window.toggleSidebar = function () {
        var sidebar = document.getElementById('app-sidebar');
        if (!sidebar) return;
        sidebar.classList.toggle('sidebar-collapsed');
    };

    /* ---- 自动从 DOM 构建菜单（无服务端数据时的降级方案） ---- */
    window.buildSidebarFromConfig = function (items, activeId) {
        items = items || SIDEBAR_MENU_ITEMS;
        var nav = document.getElementById('sidebar-nav');
        if (!nav) return;

        // 只在 DOM 中没有 nav-item 时才构建（避免重复）
        if (nav.querySelector('.nav-item')) return;

        var html = '';
        items.forEach(function (item) {
            var isActive = activeId && item.id === activeId ? ' active' : '';
            html += '<a href="' + item.url + '" class="nav-item' + isActive + '" data-nav-id="' + item.id + '" onclick="sidebarNavigate(\'' + item.url + '\'); return false;">';
            html += '<span class="nav-icon">' + item.icon + '</span>';
            html += '<span class="nav-label">' + item.label + '</span>';
            html += '</a>';
        });
        nav.innerHTML = html;
    };

    /* ---- 初始化 ---- */
    document.addEventListener('DOMContentLoaded', function () {
        initSidebarHighlight();
    });
})();
