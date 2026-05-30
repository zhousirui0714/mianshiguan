/* ==========================================
   3d-effects.js — 游戏级 3D 视觉效果 (ES Module)
   优先级 1: 3D 粒子背景（Three.js）
   优先级 2: 徽章解锁特效（Canvas 2D + CSS）
   优先级 3: 首页英雄区 3D 标题（Three.js）
   ==========================================
   使用方式：
   1. 在 HTML 中添加 importmap：
      <script type="importmap">{ "imports": { "three": "...", "three/addons/": "..." } }</script>
   2. <script type="module" src="/static/js/3d-effects.js"></script>
   3. Three.js Canvas 自动插入到 body 开头
   ========================================== */

import * as THREE from 'three';
import { FontLoader } from 'three/addons/loaders/FontLoader.js';
import { TextGeometry } from 'three/addons/geometries/TextGeometry.js';

(function () {
  'use strict';

  // -------- 环境检测 --------
  var isMobile =
    window.innerWidth < 768 ||
    /Mobi|Android|iPhone|iPad/i.test(navigator.userAgent);
  var prefersReducedMotion = false;
  try {
    prefersReducedMotion = window.matchMedia(
      '(prefers-reduced-motion: reduce)'
    ).matches;
  } catch (_) {}

  var THREE_INITIALIZED = false;
  var particlesInstance = null;
  var textInstance = null;

  /* -------- 避免重复初始化 -------- */
  if (document.querySelector('#three-canvas')) {
    THREE_INITIALIZED = true;
  }

  /* ==========================================
     优先级 1：3D 粒子背景
     带有鼠标视差效果的蓝紫色粒子场
     ========================================== */

  function createParticleField() {
    if (THREE_INITIALIZED || prefersReducedMotion) return null;
    if (document.querySelector('#three-canvas')) return null;

    var scene = new THREE.Scene();
    var camera = new THREE.PerspectiveCamera(
      75,
      window.innerWidth / window.innerHeight,
      0.1,
      1000
    );
    var renderer = new THREE.WebGLRenderer({
      alpha: true,
      antialias: !isMobile,
    });
    renderer.setSize(window.innerWidth, window.innerHeight);
    renderer.setPixelRatio(Math.min(window.devicePixelRatio, isMobile ? 1 : 2));
    renderer.setClearColor(0x000000, 0);

    var canvas = renderer.domElement;
    canvas.id = 'three-canvas';
    canvas.style.position = 'fixed';
    canvas.style.inset = '0';
    canvas.style.zIndex = '-1';
    canvas.style.pointerEvents = 'none';
    canvas.style.width = '100%';
    canvas.style.height = '100%';

    // Insert before aurora-bg or at body start
    var aurora = document.querySelector('.aurora-bg');
    if (aurora) {
      aurora.parentNode.insertBefore(canvas, aurora);
    } else {
      document.body.insertBefore(
        canvas,
        document.body.firstChild
      );
    }

    camera.position.z = 120;

    // -------- 粒子 --------
    var count = isMobile ? 300 : 800;
    var geometry = new THREE.BufferGeometry();
    var positions = new Float32Array(count * 3);
    var colors = new Float32Array(count * 3);
    var sizes = new Float32Array(count);

    var colorA = new THREE.Color('#6366F1'); // 靛蓝
    var colorB = new THREE.Color('#8B5CF6'); // 紫色

    for (var i = 0; i < count; i++) {
      var radius = 60 + Math.random() * 40;
      var theta = Math.random() * Math.PI * 2;
      var phi = Math.acos(2 * Math.random() - 1);

      positions[i * 3] = radius * Math.sin(phi) * Math.cos(theta);
      positions[i * 3 + 1] = radius * Math.sin(phi) * Math.sin(theta);
      positions[i * 3 + 2] = radius * Math.cos(phi);

      var mix = Math.random();
      var c = colorA.clone().lerp(colorB, mix);
      colors[i * 3] = c.r;
      colors[i * 3 + 1] = c.g;
      colors[i * 3 + 2] = c.b;

      sizes[i] = Math.random() * 2.5 + 0.5;
    }

    geometry.setAttribute('position', new THREE.BufferAttribute(positions, 3));
    geometry.setAttribute('color', new THREE.BufferAttribute(colors, 3));
    geometry.setAttribute('size', new THREE.BufferAttribute(sizes, 1));

    // 自定义着色器材质（圆点）
    var material = new THREE.PointsMaterial({
      size: isMobile ? 0.15 : 0.25,
      vertexColors: true,
      transparent: true,
      opacity: 0.8,
      blending: THREE.AdditiveBlending,
      depthWrite: false,
      sizeAttenuation: true,
    });

    var particles = new THREE.Points(geometry, material);
    scene.add(particles);

    // 第二层：更小更远的粒子
    var count2 = Math.floor(count * 0.4);
    var geo2 = new THREE.BufferGeometry();
    var pos2 = new Float32Array(count2 * 3);
    for (var j = 0; j < count2; j++) {
      pos2[j * 3] = (Math.random() - 0.5) * 200;
      pos2[j * 3 + 1] = (Math.random() - 0.5) * 200;
      pos2[j * 3 + 2] = (Math.random() - 0.5) * 200 - 50;
    }
    geo2.setAttribute('position', new THREE.BufferAttribute(pos2, 3));
    var mat2 = new THREE.PointsMaterial({
      size: 0.08,
      color: 0x6366f1,
      transparent: true,
      opacity: 0.3,
      blending: THREE.AdditiveBlending,
      depthWrite: false,
      sizeAttenuation: true,
    });
    var particles2 = new THREE.Points(geo2, mat2);
    scene.add(particles2);

    // -------- 鼠标视差 --------
    var mouseX = 0;
    var mouseY = 0;
    var targetX = 0;
    var targetY = 0;

    function onMouseMove(e) {
      mouseX = (e.clientX / window.innerWidth) * 2 - 1;
      mouseY = -(e.clientY / window.innerHeight) * 2 + 1;
    }

    // Only track mouse on non-mobile
    if (!isMobile) {
      document.addEventListener('mousemove', onMouseMove);
    }

    // -------- Resize --------
    function onResize() {
      camera.aspect = window.innerWidth / window.innerHeight;
      camera.updateProjectionMatrix();
      renderer.setSize(window.innerWidth, window.innerHeight);
    }
    window.addEventListener('resize', onResize);

    // -------- 动画循环 --------
    function animate() {
      requestAnimationFrame(animate);

      // 缓慢自转
      particles.rotation.y += 0.0008;
      particles.rotation.x += 0.0002;
      particles2.rotation.y += 0.0004;

      // 鼠标视差平滑跟随
      if (!isMobile) {
        targetX += (mouseX * 0.3 - targetX) * 0.05;
        targetY += (mouseY * 0.3 - targetY) * 0.05;
        particles.rotation.x += targetY * 0.0003;
        particles.rotation.y += targetX * 0.0003;
      }

      renderer.render(scene, camera);
    }

    animate();

    THREE_INITIALIZED = true;

    return {
      scene: scene,
      camera: camera,
      renderer: renderer,
      particles: particles,
      destroy: function () {
        document.removeEventListener('mousemove', onMouseMove);
        window.removeEventListener('resize', onResize);
        renderer.dispose();
        if (canvas.parentNode) canvas.parentNode.removeChild(canvas);
        THREE_INITIALIZED = false;
      },
    };
  }

  /* ==========================================
     优先级 3：3D 标题文字
     金属质感的 "百工模拟考场"
     ========================================== */

  function create3DTitle(container) {
    if (
      prefersReducedMotion ||
      !container ||
      typeof THREE === 'undefined'
    )
      return;

    // 如果容器已有 canvas 则跳过
    if (container.querySelector('canvas')) return;

    var width = container.clientWidth || 800;
    var height = container.clientHeight || 320;
    if (isMobile) height = 200;

    var scene = new THREE.Scene();
    var camera = new THREE.PerspectiveCamera(45, width / height, 0.1, 1000);
    var renderer = new THREE.WebGLRenderer({
      alpha: true,
      antialias: !isMobile,
    });
    renderer.setSize(width, height);
    renderer.setPixelRatio(Math.min(window.devicePixelRatio, isMobile ? 1 : 2));
    renderer.setClearColor(0x000000, 0);
    renderer.toneMapping = THREE.ACESFilmicToneMapping;
    renderer.toneMappingExposure = 1.2;

    container.appendChild(renderer.domElement);

    // -------- 灯光 --------
    var ambientLight = new THREE.AmbientLight(0x404060, 0.5);
    scene.add(ambientLight);

    var dirLight = new THREE.DirectionalLight(0xffffff, 1.2);
    dirLight.position.set(2, 3, 4);
    scene.add(dirLight);

    var dirLight2 = new THREE.DirectionalLight(0x6366f1, 0.6);
    dirLight2.position.set(-2, -1, 3);
    scene.add(dirLight2);

    var rimLight = new THREE.DirectionalLight(0x8b5cf6, 0.4);
    rimLight.position.set(0, -2, -3);
    scene.add(rimLight);

    camera.position.z = 5;

    // -------- 加载字体 + 创建文字 --------
    var loader = new FontLoader();
    var fontUrl =
      'https://unpkg.com/three@0.160.0/examples/fonts/helvetiker_regular.typeface.json';

    // For Chinese text, we use a simple billboarded text approach
    // since TextGeometry doesn't support CJK characters well
    // Instead, create a visually impressive scene with floating geometric shapes
    // and render Chinese text as a sprite overlay

    // Create a torus knot (cool geometric shape)
    var knotGeo = new THREE.TorusKnotGeometry(1.2, 0.4, 128, 16);
    var knotMat = new THREE.MeshPhysicalMaterial({
      color: 0x6366f1,
      metalness: 0.7,
      roughness: 0.2,
      emissive: 0x312e81,
      emissiveIntensity: 0.15,
      clearcoat: 0.3,
      clearcoatRoughness: 0.4,
    });
    var knot = new THREE.Mesh(knotGeo, knotMat);
    knot.position.x = -2.5;
    knot.position.y = 0.3;
    scene.add(knot);

    // Secondary smaller knot
    var knotGeo2 = new THREE.TorusKnotGeometry(0.6, 0.2, 64, 8);
    var knotMat2 = new THREE.MeshPhysicalMaterial({
      color: 0x8b5cf6,
      metalness: 0.5,
      roughness: 0.3,
      emissive: 0x4c1d95,
      emissiveIntensity: 0.1,
    });
    var knot2 = new THREE.Mesh(knotGeo2, knotMat2);
    knot2.position.x = 2.8;
    knot2.position.y = -0.5;
    scene.add(knot2);

    // Floating rings
    var ringGeo = new THREE.TorusGeometry(1.0, 0.03, 16, 48);
    var ringMat = new THREE.MeshPhysicalMaterial({
      color: 0x818cf8,
      metalness: 0.8,
      roughness: 0.1,
      transparent: true,
      opacity: 0.4,
    });
    var ring = new THREE.Mesh(ringGeo, ringMat);
    ring.position.x = 0.5;
    ring.position.y = -0.8;
    ring.rotation.x = Math.PI * 0.3;
    scene.add(ring);

    // Small floating particles around
    var sparkleCount = 50;
    var sparkleGeo = new THREE.BufferGeometry();
    var sparklePos = new Float32Array(sparkleCount * 3);
    for (var i = 0; i < sparkleCount; i++) {
      var theta = Math.random() * Math.PI * 2;
      var r = 2 + Math.random() * 3;
      sparklePos[i * 3] = Math.cos(theta) * r;
      sparklePos[i * 3 + 1] = (Math.random() - 0.5) * 2;
      sparklePos[i * 3 + 2] = Math.sin(theta) * r;
    }
    sparkleGeo.setAttribute('position', new THREE.BufferAttribute(sparklePos, 3));
    var sparkleMat = new THREE.PointsMaterial({
      size: 0.05,
      color: 0xa5b4fc,
      transparent: true,
      opacity: 0.6,
      blending: THREE.AdditiveBlending,
    });
    var sparkles = new THREE.Points(sparkleGeo, sparkleMat);
    scene.add(sparkles);

    // -------- 鼠标交互 --------
    var mouseX = 0;
    var mouseY = 0;

    function onMouseMove(e) {
      var rect = container.getBoundingClientRect();
      mouseX = ((e.clientX - rect.left) / rect.width) * 2 - 1;
      mouseY = -((e.clientY - rect.top) / rect.height) * 2 + 1;

      // Hover glow: when mouse is near center, intensify emissive
      var dist = Math.sqrt(mouseX * mouseX + mouseY * mouseY);
      var intensity = Math.max(0, 1 - dist) * 0.3;
      knotMat.emissiveIntensity = 0.15 + intensity;
    }

    // 监听 canvas 而非 container，避免 container pointer-events: none 的影响
    renderer.domElement.addEventListener('mousemove', onMouseMove);
    renderer.domElement.addEventListener('mouseleave', function () {
      knotMat.emissiveIntensity = 0.15;
    });

    // -------- Resize --------
    function onResize() {
      var w = container.clientWidth || 800;
      var h = container.clientHeight || (isMobile ? 200 : 320);
      camera.aspect = w / h;
      camera.updateProjectionMatrix();
      renderer.setSize(w, h);
    }
    window.addEventListener('resize', onResize);

    // -------- 动画 --------
    function animate() {
      textInstance = requestAnimationFrame(animate);

      // 缓慢旋转
      knot.rotation.x += 0.005;
      knot.rotation.y += 0.01;
      knot2.rotation.x += 0.008;
      knot2.rotation.y -= 0.006;
      ring.rotation.z += 0.008;
      ring.rotation.x += 0.004;
      sparkles.rotation.y += 0.003;

      // 鼠标跟随
      targetRotX += (mouseY * 0.2 - targetRotX) * 0.05;
      targetRotY += (mouseX * 0.2 - targetRotY) * 0.05;

      var group = new THREE.Group();
      group.add(knot, knot2, ring, sparkles);
      // Apply rotation to each individually instead
      // We already rotate each object, the camera perspective shift for mouse
      camera.position.x += (mouseX * 0.3 - camera.position.x) * 0.03;
      camera.position.y += (mouseY * 0.3 - camera.position.y) * 0.03;
      camera.lookAt(0, 0, 0);

      renderer.render(scene, camera);
    }

    animate();

    return {
      scene: scene,
      camera: camera,
      renderer: renderer,
      destroy: function () {
        container.removeEventListener('mousemove', onMouseMove);
        window.removeEventListener('resize', onResize);
        if (textInstance) cancelAnimationFrame(textInstance);
        renderer.dispose();
      },
    };
  }

  /* ==========================================
     优先级 2：徽章解锁粒子爆发 (Canvas 2D)
     类似《原神》抽卡出金特效的简化版
     ========================================== */

  function triggerBadgeBurst(centerX, centerY) {
    if (prefersReducedMotion) return;

    var canvas = document.createElement('canvas');
    canvas.className = 'burst-canvas';
    canvas.width = window.innerWidth;
    canvas.height = window.innerHeight;
    document.body.appendChild(canvas);

    var ctx = canvas.getContext('2d');
    var particles = [];
    var duration = 2000; // 2 秒
    var startTime = performance.now();

    // 金色粒子爆发
    var count = 80;
    for (var i = 0; i < count; i++) {
      var angle = Math.random() * Math.PI * 2;
      var speed = 100 + Math.random() * 300;
      var size = 2 + Math.random() * 4;
      var hue = 40 + Math.random() * 20; // 金色系 40-60
      particles.push({
        x: centerX,
        y: centerY,
        vx: Math.cos(angle) * speed,
        vy: Math.sin(angle) * speed,
        size: size,
        alpha: 0.8 + Math.random() * 0.2,
        hue: hue,
        life: 1,
        decay: 0.3 + Math.random() * 0.5,
      });
    }

    // 星光粒子（小而亮）
    for (var j = 0; j < 30; j++) {
      var a2 = Math.random() * Math.PI * 2;
      var s2 = 200 + Math.random() * 400;
      particles.push({
        x: centerX,
        y: centerY,
        vx: Math.cos(a2) * s2,
        vy: Math.sin(a2) * s2,
        size: 1 + Math.random() * 2,
        alpha: 1,
        hue: 50,
        life: 1,
        decay: 0.3 + Math.random() * 0.4,
      });
    }

    // 光晕扩张
    var ringRadius = 0;
    var ringMax = 100 + Math.random() * 50;

    var animId;

    function draw() {
      var elapsed = performance.now() - startTime;
      var progress = Math.min(elapsed / duration, 1);

      ctx.clearRect(0, 0, canvas.width, canvas.height);

      // 绘制中心光晕
      var glowProgress = Math.min(progress * 3, 1);
      ringRadius = ringMax * glowProgress;
      var ringAlpha = (1 - glowProgress) * 0.5;

      var gradient = ctx.createRadialGradient(
        centerX,
        centerY,
        0,
        centerX,
        centerY,
        ringRadius
      );
      gradient.addColorStop(
        0,
        'rgba(255, 215, 0, ' + ringAlpha * 0.6 + ')'
      );
      gradient.addColorStop(
        0.5,
        'rgba(255, 215, 0, ' + ringAlpha * 0.3 + ')'
      );
      gradient.addColorStop(1, 'rgba(255, 215, 0, 0)');
      ctx.fillStyle = gradient;
      ctx.beginPath();
      ctx.arc(centerX, centerY, ringRadius, 0, Math.PI * 2);
      ctx.fill();

      // 外圈光晕环
      ctx.strokeStyle =
        'rgba(255, 215, 0, ' + ringAlpha * 0.4 + ')';
      ctx.lineWidth = 2;
      ctx.beginPath();
      ctx.arc(centerX, centerY, ringRadius, 0, Math.PI * 2);
      ctx.stroke();

      // 绘制粒子
      for (var i = particles.length - 1; i >= 0; i--) {
        var p = particles[i];
        p.x += p.vx * 0.016;
        p.y += p.vy * 0.016;
        p.vy += 60 * 0.016; // 轻微重力
        p.life -= p.decay * 0.016;
        p.alpha = Math.max(0, p.life);

        if (p.life <= 0) {
          particles.splice(i, 1);
          continue;
        }

        ctx.save();
        ctx.globalAlpha = p.alpha;
        ctx.shadowColor = 'hsla(' + p.hue + ', 100%, 70%, 0.5)';
        ctx.shadowBlur = p.size * 4;
        ctx.fillStyle = 'hsla(' + p.hue + ', 100%, 70%, 1)';
        ctx.beginPath();
        ctx.arc(p.x, p.y, p.size * p.life, 0, Math.PI * 2);
        ctx.fill();
        ctx.restore();
      }

      // 绘制星形射线（从中心放射的光线）
      if (progress < 0.6) {
        var rayCount = 12;
        var rayProgress = progress / 0.6;
        for (var r = 0; r < rayCount; r++) {
          var ra = (r / rayCount) * Math.PI * 2 + progress * 0.5;
          var rayLen = 150 * rayProgress;
          ctx.strokeStyle =
            'rgba(255, 215, 0, ' +
            (1 - rayProgress) * 0.3 +
            ')';
          ctx.lineWidth = 2;
          ctx.beginPath();
          ctx.moveTo(centerX, centerY);
          ctx.lineTo(
            centerX + Math.cos(ra) * rayLen,
            centerY + Math.sin(ra) * rayLen
          );
          ctx.stroke();
        }
      }

      if (progress < 1) {
        animId = requestAnimationFrame(draw);
      } else {
        ctx.clearRect(0, 0, canvas.width, canvas.height);
        if (canvas.parentNode) canvas.parentNode.removeChild(canvas);
      }
    }

    animId = requestAnimationFrame(draw);
  }

  /* ==========================================
     徽章光环激活
     ========================================== */

  function activateBadgeHalo(badgeElement) {
    if (!badgeElement || prefersReducedMotion) return;

    // 添加光环元素
    var halo = document.createElement('div');
    halo.className = 'badge-halo active glow-pulse';
    badgeElement.style.position = 'relative';
    badgeElement.appendChild(halo);

    // 3 秒后淡化移除
    setTimeout(function () {
      halo.style.opacity = '0';
      halo.style.transition = 'opacity 0.5s';
      setTimeout(function () {
        if (halo.parentNode) halo.parentNode.removeChild(halo);
      }, 500);
    }, 3000);
  }

  /* ==========================================
     徽章特效完整入口（供 interview_result.html 调用）
     使用方式：
       import('/static/js/3d-effects.js').then(m => m.triggerBadgeUnlock(el, rect))
     ========================================== */

  function triggerBadgeUnlock(badgeElement) {
    if (!badgeElement) return;

    // 计算徽章中心坐标
    var rect = badgeElement.getBoundingClientRect();
    var centerX = rect.left + rect.width / 2;
    var centerY = rect.top + rect.height / 2;

    // 粒子爆发
    triggerBadgeBurst(centerX, centerY);

    // 激活光环
    setTimeout(function () {
      activateBadgeHalo(badgeElement);
    }, 300);
  }

  /* ==========================================
     自动初始化 — 检测页面类型并启动对应效果
     ========================================== */

  function init() {
    if (prefersReducedMotion) return;

    // 检查是否有首页的 3D 标题容器
    var heroContainer = document.querySelector('.hero-3d-container');
    if (heroContainer) {
      // 懒启动：等待 DOM 稳定
      setTimeout(function () {
        create3DTitle(heroContainer);
      }, 200);

      // 首页也启动粒子背景
      setTimeout(function () {
        if (!particlesInstance) {
          particlesInstance = createParticleField();
        }
      }, 100);
    } else {
      // 非首页：仅当页面有 .has-3d-bg 标记时才启动粒子背景
      var has3dFlag = document.querySelector('[data-3d-bg="particles"]');
      if (has3dFlag && !particlesInstance) {
        setTimeout(function () {
          particlesInstance = createParticleField();
        }, 100);
      }
    }
  }

  // 等待 DOM 准备
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }

  /* ==========================================
     导出全局 API
     ========================================== */
  window.ThreeDEffects = {
    createParticleField: createParticleField,
    create3DTitle: create3DTitle,
    triggerBadgeBurst: triggerBadgeBurst,
    activateBadgeHalo: activateBadgeHalo,
    triggerBadgeUnlock: triggerBadgeUnlock,
  };
})();
