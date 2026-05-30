/* ==========================================
   effects.js — 高级动效
   优先级 3: 数字滚动动画（export 给其他页面用）
   优先级 5: 粒子背景（Canvas）
   ========================================== */

(function () {
  'use strict';

  /* -------- 减少动效偏好检测 -------- */
  var prefersReducedMotion = false;
  try {
    prefersReducedMotion = window.matchMedia(
      '(prefers-reduced-motion: reduce)'
    ).matches;
  } catch (_) {
    /* 降级 */
  }

  /* ==========================================
     优先级 3：数字滚动动画
     用法: Effects.animateNumber(el, start, end, duration, suffix)
     ========================================== */

  function animateNumber(el, start, end, duration, suffix) {
    if (prefersReducedMotion) {
      el.textContent = Math.round(end) + (suffix || '');
      return function () {};
    }

    if (!el) return function () {};
    duration = duration || 2000;
    suffix = suffix || '';

    var startTime = null;
    var animationId = null;

    function easing(t) {
      // easeOutExpo: 先快后慢，感觉更自然
      return t === 1 ? 1 : 1 - Math.pow(2, -10 * t);
    }

    function step(ts) {
      if (!startTime) startTime = ts;
      var progress = Math.min((ts - startTime) / duration, 1);
      var eased = easing(progress);
      var current = Math.round(start + (end - start) * eased);
      el.textContent = current + suffix;
      if (progress < 1) {
        animationId = requestAnimationFrame(step);
      } else {
        el.textContent = Math.round(end) + suffix;
      }
    }

    animationId = requestAnimationFrame(step);

    return function cancel() {
      if (animationId) cancelAnimationFrame(animationId);
    };
  }

  /* ==========================================
     优先级 3（附加）：批量数字滚动 — 自动扫描 [data-animate-number]
     属性: data-value="85" data-duration="2000" data-suffix="分"
     ========================================== */

  function initAnimatedNumbers() {
    if (prefersReducedMotion) return;
    var els = document.querySelectorAll('[data-animate-number]');
    for (var i = 0; i < els.length; i++) {
      var el = els[i];
      var end = parseFloat(el.getAttribute('data-value')) || 0;
      var dur = parseFloat(el.getAttribute('data-duration')) || 2000;
      var suffix = el.getAttribute('data-suffix') || '';
      // Start from 0
      animateNumber(el, 0, end, dur, suffix);
    }
  }

  /* ==========================================
     优先级 5：粒子背景（Canvas）
     用法: Effects.initParticles(canvasId)
     自动在带有 data-particles 属性的元素后插入 canvas
     ========================================== */

  var particleInstances = [];

  function initParticles(containerSelector) {
    if (prefersReducedMotion) return;

    var container =
      (containerSelector &&
        document.querySelector(containerSelector)) ||
      document.querySelector('[data-particles]') ||
      document.querySelector('.aurora-bg');

    if (!container) return;

    // 检查是否已存在 canvas
    if (container.querySelector('.particle-canvas')) return;

    var canvas = document.createElement('canvas');
    canvas.className = 'particle-canvas';
    canvas.style.cssText =
      'position:fixed;inset:0;z-index:0;pointer-events:none;width:100%;height:100%;';
    document.body.insertBefore(canvas, document.body.firstChild);

    var ctx = canvas.getContext('2d');
    var particles = [];
    var animId = null;
    var W, H;

    function resize() {
      W = canvas.width = window.innerWidth;
      H = canvas.height = window.innerHeight;
    }

    window.addEventListener('resize', resize);
    resize();

    // 创建粒子：5-10 个
    var count = Math.min(Math.max(5, Math.floor(W / 300)), 10);

    for (var i = 0; i < count; i++) {
      particles.push({
        x: Math.random() * W,
        y: Math.random() * H,
        r: Math.random() * 3 + 1.5, // 半径 1.5-4.5px
        dx: (Math.random() - 0.5) * 0.3,
        dy: (Math.random() - 0.5) * 0.3,
        alpha: Math.random() * 0.15 + 0.05, // 极低透明度 0.05-0.2
        hue: Math.random() < 0.5 ? 239 : 260, // 蓝紫色系
      });
    }

    function draw() {
      ctx.clearRect(0, 0, W, H);

      for (var i = 0; i < particles.length; i++) {
        var p = particles[i];
        p.x += p.dx;
        p.y += p.dy;

        // 边界回弹
        if (p.x < -20) p.x = W + 20;
        if (p.x > W + 20) p.x = -20;
        if (p.y < -20) p.y = H + 20;
        if (p.y > H + 20) p.y = -20;

        ctx.beginPath();
        ctx.arc(p.x, p.y, p.r, 0, Math.PI * 2);
        ctx.fillStyle = 'hsla(' + p.hue + ', 70%, 70%, ' + p.alpha + ')';
        ctx.fill();

        // 微弱连接线（距离 < 200px 时）
        for (var j = i + 1; j < particles.length; j++) {
          var p2 = particles[j];
          var dx = p.x - p2.x;
          var dy = p.y - p2.y;
          var dist = Math.sqrt(dx * dx + dy * dy);
          if (dist < 200) {
            ctx.beginPath();
            ctx.moveTo(p.x, p.y);
            ctx.lineTo(p2.x, p2.y);
            ctx.strokeStyle =
              'hsla(239, 60%, 70%, ' +
              (0.03 * (1 - dist / 200)) +
              ')';
            ctx.lineWidth = 0.5;
            ctx.stroke();
          }
        }
      }

      animId = requestAnimationFrame(draw);
    }

    animId = requestAnimationFrame(draw);

    var instance = {
      canvas: canvas,
      ctx: ctx,
      destroy: function () {
        if (animId) cancelAnimationFrame(animId);
        window.removeEventListener('resize', resize);
        if (canvas.parentNode) canvas.parentNode.removeChild(canvas);
      },
    };

    particleInstances.push(instance);
    return instance;
  }

  /* ==========================================
     自动初始化（DOMContentLoaded）
     ========================================== */

  function init() {
    // 页面转场：给 body 内首个容器添加 page-wrapper 类
    var main = document.querySelector('#app, .container, main, .main-content');
    if (main && !main.classList.contains('page-wrapper')) {
      main.classList.add('page-wrapper');
    }

    // 自动初始化数字滚动
    initAnimatedNumbers();

    // 延迟粒子初始化（让页面先渲染）
    setTimeout(function () {
      initParticles();
    }, 100);
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }

  /* ==========================================
     Effects 全局 API
     ========================================== */
  window.Effects = {
    animateNumber: animateNumber,
    initAnimatedNumbers: initAnimatedNumbers,
    initParticles: initParticles,
  };
})();
