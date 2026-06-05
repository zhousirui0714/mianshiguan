/**
 * 侧边栏组件 — 交互逻辑
 * 依赖：sidebar.css（样式）
 * 使用：在模板中加载本脚本后，侧边栏自动获得导航和折叠能力
 */

(function () {
    'use strict';

    /* ---- 菜单项配置 ---- */
    var HOME_SVG = '<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><path d="M3 12l9-9 9 9"/><path d="M5 10v9a1 1 0 001 1h3v-5a1 1 0 011-1h2a1 1 0 011 1v5h3a1 1 0 001-1v-9"/></svg>';
    var DOC_SVG = '<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><path d="M14 2H6a2 2 0 00-2 2v16a2 2 0 002 2h12a2 2 0 002-2V8z"/><polyline points="14 2 14 8 20 8"/></svg>';
    var CLOCK_SVG = '<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><circle cx="12" cy="12" r="10"/><polyline points="12 6 12 12 16 14"/></svg>';
    var TREND_SVG = '<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><polyline points="23 6 13.5 15.5 8.5 10.5 1 18"/><polyline points="17 6 23 6 23 12"/></svg>';
    var EDIT_SVG = '<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><path d="M11 4H4a2 2 0 00-2 2v14a2 2 0 002 2h14a2 2 0 002-2v-7"/><path d="M18.5 2.5a2.121 2.121 0 013 3L12 15l-4 1 1-4 9.5-9.5z"/></svg>';
    var STAR_SVG = '<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><path d="M12 2l3.09 6.26L22 9.27l-5 4.87 1.18 6.88L12 17.77l-6.18 3.25L7 14.14 2 9.27l6.91-1.01L12 2z"/></svg>';

    var SIDEBAR_MENU_ITEMS = [
        { id: 'home',     label: '首页',     icon: HOME_SVG, url: '/' },
        { id: 'questions',label: '题库中心', icon: DOC_SVG, url: '/question-bank' },
        { id: 'learning', label: '学习计划', icon: CLOCK_SVG, url: '/learning-plan' },
        { id: 'growth',   label: '成长中心', icon: TREND_SVG, url: '/growth' },
        { id: 'mock',     label: '模拟练习', icon: EDIT_SVG, url: '/mock-exam' },
        { id: 'badges',   label: '成就徽章', icon: STAR_SVG, url: '/badges' }
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
