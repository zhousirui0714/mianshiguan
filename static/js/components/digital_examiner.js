/**
 * 2D 数字人考官组件
 * ====================================
 * 纯前端实现，无外部依赖。
 * 使用 CSS 绘制的占位考官作为默认显示（即开即用）。
 * 当立绘图片存在时自动升级为 PNG 图片模式。
 *
 * 用法:
 *   Examiner.init({ scenario: 'job_interview', containerId: 'examiner-container' });
 *   Examiner.setExpression('smile');
 *   Examiner.startSpeaking();
 *   Examiner.stopSpeaking();
 */
;(function (root) {
  'use strict';

  /* ========== 常量 ========== */

  var EXPRESSIONS = ['neutral', 'smile', 'thinking', 'encouraging', 'ending'];

  var LABEL_MAP = {
    neutral:      '中性',
    smile:        '微笑',
    thinking:     '思考中...',
    encouraging:  '加油！',
    ending:       '面试结束',
  };

  var EMOTION_MAP = {
    neutral:      'neutral',
    happy:        'smile',
    encouraging:  'encouraging',
    thinking:     'thinking',
    approving:    'smile',
    disagree:     'neutral',
    confused:     'thinking',
    goodbye:      'ending',
  };

  var SCENE_ALIAS = {
    job_interview:  'job',
    teacher_cert:   'teaching',
    ielts_speaking: 'ielts',
    civil_service:  'civil',
    graduate_school:'graduate',
    mba_interview:  'mba',
  };

  var SCENE_GENDER = {
    job_interview:  'male',
    teacher_cert:   'female',
    ielts_speaking: 'male',
    civil_service:  'male',
    graduate_school:'male',
    mba_interview:  'male',
  };

  var GENDERS = ['male', 'female'];

  /* ========== 状态 ========== */

  var state = {
    initialized: false,
    scenario: 'job_interview',
    sceneAlias: 'job',
    gender: 'male',
    currentExpression: 'neutral',
    containerId: 'examiner-container',
    // 始终以 placeholder 模式启动，图片作为渐进增强
    usingPlaceholder: true,
    speaking: false,
  };

  var dom = {};

  // 眨眼计时器
  var _blinkTimer = null;
  var _expressionTimer = null;

  /* ========== 主对象 ========== */

  var Examiner = {

    /**
     * 初始化考官组件
     */
    init: function (opts) {
      opts = opts || {};
      state.scenario = opts.scenario || 'job_interview';
      state.sceneAlias = SCENE_ALIAS[state.scenario] || 'job';
      state.gender = opts.gender || SCENE_GENDER[state.scenario] || 'male';
      state.containerId = opts.containerId || 'examiner-container';
      state.usingPlaceholder = true;

      this._buildDOM(opts.examinerInfo || {});
      this._startBlink();
      this._tryLoadImages();

      state.initialized = true;
      this.setExpression('neutral');

      console.log('[Examiner] initialized, scenario=' + state.scenario +
                  ', gender=' + state.gender +
                  ', usingPlaceholder=' + state.usingPlaceholder);
    },

    /* ---- 公开 API ---- */

    setExpression: function (expr) {
      if (EXPRESSIONS.indexOf(expr) === -1) return;
      state.currentExpression = expr;
      this._updateImage(expr);
      this._updateGlassState(expr);
      if (dom.label) {
        dom.label.textContent = LABEL_MAP[expr] || expr;
      }
      this._updateMouthPath(expr);
    },

    startSpeaking: function () {
      if (state.speaking) return;
      state.speaking = true;
      if (dom.speakingIndicator) {
        dom.speakingIndicator.classList.add('active');
      }
    },

    stopSpeaking: function () {
      state.speaking = false;
      if (dom.speakingIndicator) {
        dom.speakingIndicator.classList.remove('active');
      }
    },

    setEmotion: function (emotion) {
      var expr = EMOTION_MAP[emotion] || 'neutral';
      this.setExpression(expr);
    },

    destroy: function () {
      if (_blinkTimer) { clearTimeout(_blinkTimer); _blinkTimer = null; }
      if (_expressionTimer) { clearTimeout(_expressionTimer); _expressionTimer = null; }
      var container = document.getElementById(state.containerId);
      if (container) container.innerHTML = '';
      state.initialized = false;
      dom = {};
    },

    getState: function () {
      return {
        scenario: state.scenario,
        expression: state.currentExpression,
        speaking: state.speaking,
        usingPlaceholder: state.usingPlaceholder,
      };
    },

    /* ---- 内部方法 ---- */

    /** 构建 DOM：始终先画 CSS 占位 */
    _buildDOM: function (info) {
      var container = document.getElementById(state.containerId);
      if (!container) {
        console.error('[Examiner] Container #' + state.containerId + ' not found');
        return;
      }
      container.innerHTML = '';

      var glass = document.createElement('div');
      glass.className = 'examiner-glass';

      // ---- 角色区域 ----
      var character = document.createElement('div');
      character.className = 'examiner-character';
      character.id = state.containerId + '-character';

      var imageWrap = document.createElement('div');
      imageWrap.className = 'examiner-image';
      imageWrap.id = state.containerId + '-image';

      // img 标签（隐藏加载图片用，加载成功则显示）
      var img = document.createElement('img');
      img.style.display = 'none';
      img.alt = '考官';
      img.id = state.containerId + '-img';

      // CSS 占位立绘
      var placeholder = this._createPlaceholderDOM();
      placeholder.id = state.containerId + '-placeholder';

      imageWrap.appendChild(img);
      imageWrap.appendChild(placeholder);
      character.appendChild(imageWrap);

      // 眨眼覆盖层
      var blinkOverlay = document.createElement('div');
      blinkOverlay.className = 'examiner-blink-overlay';
      blinkOverlay.id = state.containerId + '-blink';

      // 说话动效（3 根音波条）
      var speakingIndicator = document.createElement('div');
      speakingIndicator.className = 'examiner-speaking-indicator';
      speakingIndicator.id = state.containerId + '-speaking';
      for (var i = 0; i < 3; i++) {
        var wave = document.createElement('div');
        wave.className = 'wave';
        speakingIndicator.appendChild(wave);
      }

      // 表情标签
      var label = document.createElement('div');
      label.className = 'examiner-expression-label';
      label.id = state.containerId + '-label';
      label.textContent = '中性';

      character.appendChild(blinkOverlay);
      character.appendChild(speakingIndicator);
      character.appendChild(label);

      // 呼吸包裹
      var breathe = document.createElement('div');
      breathe.className = 'examiner-breathing';
      breathe.id = state.containerId + '-breathe';
      breathe.appendChild(character);

      // ---- 考官信息 ----
      var infoEl = document.createElement('div');
      infoEl.className = 'examiner-info';

      var nameEl = document.createElement('div');
      nameEl.className = 'name';
      nameEl.id = state.containerId + '-name';
      nameEl.textContent = info.name || '考官';

      var titleEl = document.createElement('div');
      titleEl.className = 'title';
      titleEl.id = state.containerId + '-title';
      titleEl.textContent = info.title || '';

      var statusEl = document.createElement('div');
      statusEl.className = 'status';
      statusEl.id = state.containerId + '-status';
      statusEl.textContent = '等待开始';

      infoEl.appendChild(nameEl);
      infoEl.appendChild(titleEl);
      infoEl.appendChild(statusEl);

      glass.appendChild(breathe);
      glass.appendChild(infoEl);
      container.appendChild(glass);

      // 缓存 DOM
      dom.container = container;
      dom.glass = glass;
      dom.character = character;
      dom.imageWrap = imageWrap;
      dom.img = img;
      dom.placeholder = placeholder;
      dom.blinkOverlay = blinkOverlay;
      dom.speakingIndicator = speakingIndicator;
      dom.label = label;
      dom.breathe = breathe;
      dom.name = nameEl;
      dom.title = titleEl;
      dom.status = statusEl;

      this._updateGlassState('neutral');
    },

    /** 尝试加载 PNG 图片，成功后隐藏 placeholder */
    _tryLoadImages: function () {
      var self = this;
      var testExpr = 'neutral';
      var src = this._imageSrc(testExpr);

      var testImg = new Image();
      testImg.onload = function () {
        // 图片加载成功，切换到图片模式
        state.usingPlaceholder = false;
        if (dom.img) {
          dom.img.style.display = '';
          dom.img.src = self._imageSrc(state.currentExpression) + '?t=' + Date.now();
        }
        if (dom.placeholder) {
          dom.placeholder.style.display = 'none';
        }
        console.log('[Examiner] image loaded, switched to image mode');
      };
      testImg.onerror = function () {
        // 图片不存在，保持 placeholder 模式
        console.log('[Examiner] no image found, using CSS placeholder');
      };
      testImg.src = src;
    },

    /** 更新显示（图片 / 占位嘴巴） */
    _updateImage: function (expr) {
      if (!state.usingPlaceholder && dom.img) {
        dom.img.src = this._imageSrc(expr) + '?t=' + Date.now();
      }
      this._updateMouthPath(expr);
    },

    /** 更新占位嘴巴 SVG 路径 */
    _updateMouthPath: function (expr) {
      var path = document.getElementById(state.containerId + '-mouth-path');
      if (!path) return;
      var shapes = {
        neutral:      'M 4 6 Q 20 10 36 6',
        smile:        'M 4 6 Q 20 2 36 6',
        thinking:     'M 4 6 Q 20 6 36 6',
        encouraging:  'M 2 6 Q 20 0 38 6',
        ending:       'M 4 6 Q 20 12 36 6',
      };
      path.setAttribute('d', shapes[expr] || shapes.neutral);
    },

    _updateGlassState: function (expr) {
      if (!dom.glass) return;
      var prefix = 'state-';
      EXPRESSIONS.forEach(function (e) {
        dom.glass.classList.remove(prefix + e);
      });
      if (expr !== 'neutral') {
        dom.glass.classList.add(prefix + expr);
      }
    },

    _updateStatus: function (expr) {
      if (!dom.status) return;
      var texts = {
        neutral:      '等待你的回答',
        smile:        '听得开心',
        thinking:     '正在思考...',
        encouraging:  '为你加油！',
        ending:       '面试已结束',
      };
      dom.status.textContent = texts[expr] || '';
      dom.status.className = 'status ' + expr;
    },

    /** 图片路径：/static/images/examiners/examiner_{scene}_{gender}_{expr}.png */
    _imageSrc: function (expr) {
      var basePath = '/static/images/examiners/';
      return basePath + 'examiner_' + state.sceneAlias + '_' + state.gender + '_' + expr + '.png';
    },

    /** 启动眨眼 */
    _startBlink: function () {
      var self = this;
      function doBlink() {
        var target = dom.blinkOverlay;
        if (!target) return;
        target.classList.add('active');
        setTimeout(function () {
          target.classList.remove('active');
        }, 120);
        _blinkTimer = setTimeout(doBlink, 3000 + Math.random() * 2500);
      }
      _blinkTimer = setTimeout(doBlink, 1500);
    },

    /* ========================================
       CSS 占位考官 DOM 构建
       ======================================== */

    _createPlaceholderDOM: function () {
      var body = document.createElement('div');
      body.className = 'examiner-placeholder-body';
      body.setAttribute('data-scenario', state.scenario);

      // 头部
      var head = document.createElement('div');
      head.className = 'placeholder-head';

      // 头发
      var hair = document.createElement('div');
      hair.className = 'placeholder-hair';
      head.appendChild(hair);

      // 眼镜（仅在教资/考研考官显示）
      var glasses = document.createElement('div');
      glasses.className = 'placeholder-glasses';
      var bridge = document.createElement('div');
      bridge.className = 'placeholder-glasses-bridge';
      glasses.appendChild(bridge);
      head.appendChild(glasses);
      if (state.scenario !== 'teacher_cert' && state.scenario !== 'graduate_school') {
        glasses.style.display = 'none';
      }

      // 眼睛
      var eyes = document.createElement('div');
      eyes.className = 'placeholder-eyes';
      var eyeL = document.createElement('div');
      eyeL.className = 'placeholder-eye left';
      var pupilL = document.createElement('div');
      pupilL.className = 'placeholder-pupil';
      eyeL.appendChild(pupilL);
      var eyeR = document.createElement('div');
      eyeR.className = 'placeholder-eye right';
      var pupilR = document.createElement('div');
      pupilR.className = 'placeholder-pupil';
      eyeR.appendChild(pupilR);
      eyes.appendChild(eyeL);
      eyes.appendChild(eyeR);

      // 嘴唇
      var mouth = document.createElement('div');
      mouth.className = 'placeholder-mouth';
      mouth.innerHTML = '<svg viewBox="0 0 40 12" xmlns="http://www.w3.org/2000/svg">' +
        '<path class="placeholder-mouth-path" id="' + state.containerId + '-mouth-path"' +
        ' d="M 4 6 Q 20 10 36 6" /></svg>';

      head.appendChild(eyes);
      head.appendChild(mouth);

      // 颈部
      var neck = document.createElement('div');
      neck.className = 'placeholder-neck';

      // 身体
      var torso = document.createElement('div');
      torso.className = 'placeholder-body';
      var collar = document.createElement('div');
      collar.className = 'placeholder-collar';
      var tie = document.createElement('div');
      tie.className = 'placeholder-tie';
      torso.appendChild(collar);
      torso.appendChild(tie);

      body.appendChild(head);
      body.appendChild(neck);
      body.appendChild(torso);

      return body;
    },
  };

  /* ========== 暴露到全局 ========== */

  root.Examiner = Examiner;

})(window);
