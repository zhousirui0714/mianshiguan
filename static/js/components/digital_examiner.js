/**
 * 2D 数字人考官组件
 * ====================================
 * 纯前端实现，无外部依赖。
 * 使用 PNG 立绘 + CSS 动画实现表情切换与自然动效。
 * 当立绘图片不存在时自动降级为 CSS 绘制的占位考官。
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

  const EXPRESSIONS = ['neutral', 'smile', 'thinking', 'encouraging', 'ending'];

  // 表情 → 中文标签映射
  const LABEL_MAP = {
    neutral:      '中性',
    smile:        '微笑',
    thinking:     '思考中...',
    encouraging:  '加油！',
    ending:       '面试结束',
  };

  // 情绪映射（AI 情绪标签 → 组件表情）
  const EMOTION_MAP = {
    neutral:      'neutral',
    happy:        'smile',
    encouraging:  'encouraging',
    thinking:     'thinking',
    approving:    'smile',
    disagree:     'neutral',
    confused:     'thinking',
    goodbye:      'ending',
  };

  // 场景 → 场景ID（用于构建图片路径）
  const SCENE_ALIAS = {
    job_interview:  'job',
    teacher_cert:   'teaching',
    ielts_speaking: 'ielts',
    civil_service:  'civil',
    graduate_school:'graduate',
    mba_interview:  'mba',
  };

  // 公历场景名 → 头像 emoji fallback
  const SCENE_ICON = {
    job_interview:  '👔',
    teacher_cert:   '👩‍🏫',
    ielts_speaking: '🎓',
    civil_service:  '👨‍⚖️',
    graduate_school:'🎓',
    mba_interview:  '💼',
  };

  /* ========== 状态 ========== */

  let state = {
    initialized: false,
    scenario: 'job_interview',
    sceneAlias: 'job',
    currentExpression: 'neutral',
    containerId: 'examiner-container',
    hasImages: false,       // true=使用 PNG, false=使用 CSS 占位
    imageLoadFailed: false, // 所有图片加载失败则用占位
    blinkInterval: null,
    speaking: false,
  };

  let dom = {}; // 缓存的 DOM 引用

  /* ========== 主对象 ========== */

  const Examiner = {

    /**
     * 初始化考官组件
     * @param {Object} opts
     * @param {string} opts.scenario      - 场景 ID（如 job_interview）
     * @param {string} opts.containerId   - 容器 DOM id（默认 examiner-container）
     * @param {Object} opts.examinerInfo  - 可选，覆盖考官姓名/头衔/风格
     * @param {string} opts.examinerInfo.name
     * @param {string} opts.examinerInfo.title
     */
    init: function (opts) {
      opts = opts || {};
      state.scenario = opts.scenario || 'job_interview';
      state.sceneAlias = SCENE_ALIAS[state.scenario] || 'job';
      state.containerId = opts.containerId || 'examiner-container';

      // 尝试检测图片是否存在
      this._detectImages();

      // 构建 DOM
      this._buildDOM(opts.examinerInfo || {});

      // 启动自动眨眼
      this._startBlink();

      state.initialized = true;
      this.setExpression('neutral');
    },

    /* ---- 公开 API ---- */

    /** 切换表情 */
    setExpression: function (expr) {
      if (!EXPRESSIONS.includes(expr)) return;
      state.currentExpression = expr;

      // 更新图片
      this._updateImage(expr);

      // 更新玻璃边框状态
      this._updateGlassState(expr);

      // 更新表情标签
      if (dom.label) {
        dom.label.textContent = LABEL_MAP[expr] || expr;
      }

      // 更新状态文本
      this._updateStatus(expr);
    },

    /** 开始说话动效 */
    startSpeaking: function () {
      if (state.speaking) return;
      state.speaking = true;
      if (dom.speakingIndicator) {
        dom.speakingIndicator.classList.add('active');
      }
      // 说话时加快呼吸频率
      if (dom.character) {
        dom.character.style.animationDuration = '1.2s';
      }
    },

    /** 停止说话动效 */
    stopSpeaking: function () {
      state.speaking = false;
      if (dom.speakingIndicator) {
        dom.speakingIndicator.classList.remove('active');
      }
      if (dom.character) {
        dom.character.style.animationDuration = '';
      }
    },

    /** 根据 AI 情绪标签自动切换表情 */
    setEmotion: function (emotion) {
      const expr = EMOTION_MAP[emotion] || 'neutral';
      this.setExpression(expr);
    },

    /** 销毁组件 */
    destroy: function () {
      if (state.blinkInterval) {
        clearInterval(state.blinkInterval);
        state.blinkInterval = null;
      }
      const container = document.getElementById(state.containerId);
      if (container) container.innerHTML = '';
      state.initialized = false;
    },

    /** 获取当前状态 */
    getState: function () {
      return {
        scenario: state.scenario,
        expression: state.currentExpression,
        speaking: state.speaking,
        hasImages: state.hasImages,
      };
    },

    /* ---- 内部方法 ---- */

    /** 检测立绘图片是否存在 */
    _detectImages: function () {
      // 检查第一张 neutral 图片能否加载
      const img = new Image();
      const src = this._imageSrc('neutral');
      img.onload = () => { state.hasImages = true; };
      img.onerror = () => {
        if (state.imageLoadFailed === false) {
          state.imageLoadFailed = true;
          // 重新构建 DOM 使用占位模式
          this._rebuildAsPlaceholder();
        }
      };
      img.src = src;
      // 如果图片很小可能瞬间完成，但这里先默认假设有图片
      // 如果检测失败 _rebuildAsPlaceholder 会被触发
      state.hasImages = true;

      // 额外做一次预加载验证
      if (img.complete && img.naturalWidth === 0) {
        state.hasImages = false;
        state.imageLoadFailed = true;
      }
    },

    /** 构建 DOM */
    _buildDOM: function (info) {
      const container = document.getElementById(state.containerId);
      if (!container) {
        console.error('[Examiner] Container #' + state.containerId + ' not found');
        return;
      }
      container.innerHTML = '';

      // 玻璃态外层
      const glass = document.createElement('div');
      glass.className = 'examiner-glass';

      // 角色区域
      const character = document.createElement('div');
      character.className = 'examiner-character';
      character.id = state.containerId + '-character';

      // 图片/占位
      const imageWrap = document.createElement('div');
      imageWrap.className = 'examiner-image';
      imageWrap.id = state.containerId + '-image';

      // 尝试插入图片
      const img = document.createElement('img');
      img.alt = '考官';
      img.id = state.containerId + '-img';
      img.src = this._imageSrc('neutral');
      img.onerror = () => {
        // 图片加载失败，切换为 CSS 占位
        this._switchToPlaceholder();
      };
      imageWrap.appendChild(img);

      // 眨眼覆盖层（用于图片模式）
      const blinkOverlay = document.createElement('div');
      blinkOverlay.className = 'examiner-blink-overlay';
      blinkOverlay.id = state.containerId + '-blink';

      // 说话指示器
      const speakingIndicator = document.createElement('div');
      speakingIndicator.className = 'examiner-speaking-indicator';
      speakingIndicator.id = state.containerId + '-speaking';
      for (let i = 0; i < 3; i++) {
        const wave = document.createElement('div');
        wave.className = 'wave';
        speakingIndicator.appendChild(wave);
      }

      // 表情标签
      const label = document.createElement('div');
      label.className = 'examiner-expression-label';
      label.id = state.containerId + '-label';
      label.textContent = '中性';

      character.appendChild(imageWrap);
      character.appendChild(blinkOverlay);
      character.appendChild(speakingIndicator);
      character.appendChild(label);

      // 呼吸动画容器
      const breathe = document.createElement('div');
      breathe.className = 'examiner-breathing';
      breathe.id = state.containerId + '-breathe';
      breathe.appendChild(character);

      // 信息区域
      const infoEl = document.createElement('div');
      infoEl.className = 'examiner-info';

      const nameEl = document.createElement('div');
      nameEl.className = 'name';
      nameEl.id = state.containerId + '-name';
      nameEl.textContent = info.name || '考官';

      const titleEl = document.createElement('div');
      titleEl.className = 'title';
      titleEl.id = state.containerId + '-title';
      titleEl.textContent = info.title || '';

      const statusEl = document.createElement('div');
      statusEl.className = 'status';
      statusEl.id = state.containerId + '-status';
      statusEl.textContent = '等待开始';

      infoEl.appendChild(nameEl);
      infoEl.appendChild(titleEl);
      infoEl.appendChild(statusEl);

      glass.appendChild(breathe);
      glass.appendChild(infoEl);
      container.appendChild(glass);

      // 缓存 DOM 引用
      dom.container = container;
      dom.glass = glass;
      dom.character = character;
      dom.imageWrap = imageWrap;
      dom.img = img;
      dom.blinkOverlay = blinkOverlay;
      dom.speakingIndicator = speakingIndicator;
      dom.label = label;
      dom.breathe = breathe;
      dom.name = nameEl;
      dom.title = titleEl;
      dom.status = statusEl;

      this._updateGlassState('neutral');
    },

    /** 构建占位考官 DOM（覆盖图片模式） */
    _switchToPlaceholder: function () {
      if (dom.imageWrap) {
        state.hasImages = false;
        state.imageLoadFailed = true;
        dom.imageWrap.innerHTML = '';
        const placeholder = this._createPlaceholderDOM();
        dom.imageWrap.appendChild(placeholder);
        dom.placeholder = placeholder;
        this._updateImage('neutral');
      }
    },

    /** 重建为占位模式（首次检测就失败时） */
    _rebuildAsPlaceholder: function () {
      // 如果已经初始化了，只替换图片区域
      if (dom.imageWrap) {
        this._switchToPlaceholder();
        return;
      }
      // 否则重新构建
      this._buildDOM({});
    },

    /** 创建 CSS 占位立绘 DOM */
    _createPlaceholderDOM: function () {
      const body = document.createElement('div');
      body.className = 'examiner-placeholder-body';
      body.setAttribute('data-scenario', state.scenario);

      // 头部
      const head = document.createElement('div');
      head.className = 'placeholder-head';

      // 头发
      const hair = document.createElement('div');
      hair.className = 'placeholder-hair';
      head.appendChild(hair);

      // 眼镜
      const glasses = document.createElement('div');
      glasses.className = 'placeholder-glasses';
      const bridge = document.createElement('div');
      bridge.className = 'placeholder-glasses-bridge';
      glasses.appendChild(bridge);
      head.appendChild(glasses);
      // 仅在教资/考研考官显示眼镜
      if (state.scenario !== 'teacher_cert' && state.scenario !== 'graduate_school') {
        glasses.style.display = 'none';
      }

      // 眼睛
      const eyes = document.createElement('div');
      eyes.className = 'placeholder-eyes';
      const eyeL = document.createElement('div');
      eyeL.className = 'placeholder-eye left';
      const pupilL = document.createElement('div');
      pupilL.className = 'placeholder-pupil';
      eyeL.appendChild(pupilL);
      const eyeR = document.createElement('div');
      eyeR.className = 'placeholder-eye right';
      const pupilR = document.createElement('div');
      pupilR.className = 'placeholder-pupil';
      eyeR.appendChild(pupilR);
      eyes.appendChild(eyeL);
      eyes.appendChild(eyeR);

      // 眨眼覆盖
      const blink = document.createElement('div');
      blink.className = 'placeholder-blink';

      // 嘴巴（SVG）
      const mouth = document.createElement('div');
      mouth.className = 'placeholder-mouth';
      mouth.innerHTML = `<svg viewBox="0 0 40 12" xmlns="http://www.w3.org/2000/svg">
        <path class="placeholder-mouth-path" id="${state.containerId}-mouth-path"
              d="M 4 6 Q 20 10 36 6" />
      </svg>`;

      head.appendChild(eyes);
      head.appendChild(blink);
      head.appendChild(mouth);

      // 颈部
      const neck = document.createElement('div');
      neck.className = 'placeholder-neck';

      // 身体
      const torso = document.createElement('div');
      torso.className = 'placeholder-body';
      const collar = document.createElement('div');
      collar.className = 'placeholder-collar';
      const tie = document.createElement('div');
      tie.className = 'placeholder-tie';
      torso.appendChild(collar);
      torso.appendChild(tie);

      body.appendChild(head);
      body.appendChild(neck);
      body.appendChild(torso);

      return body;
    },

    /** 更新立绘图片（根据当前表情） */
    _updateImage: function (expr) {
      if (state.hasImages && dom.img) {
        dom.img.src = this._imageSrc(expr) + '?t=' + Date.now();
      }
      if (dom.placeholder) {
        this._updatePlaceholderMouth(expr);
      }
    },

    /** 更新占位考官的嘴巴形状 */
    _updatePlaceholderMouth: function (expr) {
      const path = document.getElementById(state.containerId + '-mouth-path');
      if (!path) return;
      const shapes = {
        neutral:      'M 4 6 Q 20 10 36 6',
        smile:        'M 4 6 Q 20 2 36 6',
        thinking:     'M 4 6 Q 20 6 36 6',
        encouraging:  'M 2 6 Q 20 0 38 6',
        ending:       'M 4 6 Q 20 12 36 6',
      };
      path.setAttribute('d', shapes[expr] || shapes.neutral);
    },

    /** 更新玻璃边框状态 */
    _updateGlassState: function (expr) {
      if (!dom.glass) return;
      const prefix = 'state-';
      EXPRESSIONS.forEach(function (e) {
        dom.glass.classList.remove(prefix + e);
      });
      if (expr !== 'neutral') {
        dom.glass.classList.add(prefix + expr);
      }
    },

    /** 更新状态文本 */
    _updateStatus: function (expr) {
      if (!dom.status) return;
      const statusTexts = {
        neutral:      '等待你的回答',
        smile:        '听得开心',
        thinking:     '正在思考...',
        encouraging:  '为你加油！',
        ending:       '面试已结束',
      };
      dom.status.textContent = statusTexts[expr] || '';
      dom.status.className = 'status ' + expr;
    },

    /** 构建图片路径 */
    _imageSrc: function (expr) {
      // 优先尝试多场景命名
      const basePath = '/static/images/examiners/';
      // 尝试 examiner_{sceneAlias}_{expr}.png
      return basePath + 'examiner_' + state.sceneAlias + '_' + expr + '.png';
    },

    /** 启动自动眨眼 */
    _startBlink: function () {
      if (state.blinkInterval) clearInterval(state.blinkInterval);

      const doBlink = function () {
        const blinkTarget = dom.blinkOverlay || (dom.placeholder ? dom.placeholder.querySelector('.placeholder-blink') : null);
        if (!blinkTarget) return;

        blinkTarget.classList.add('active');

        // 眨眼的闭眼时间很短
        setTimeout(function () {
          blinkTarget.classList.remove('active');
        }, 120);

        // 下一次眨眼：3-5 秒后
        const nextDelay = 3000 + Math.random() * 2500;
        state.blinkTimeout = setTimeout(doBlink, nextDelay);
      };

      // 首次眨眼延迟短一些
      state.blinkTimeout = setTimeout(doBlink, 1500);

      // 额外心跳确保持续运行（如果 timeout 被莫名取消）
      state.blinkHeartbeat = setInterval(function () {
        // 如果没有闪烁计划且没有 active blink，就调度一个
        // 实际上由递归 timeout 维持，这是后备
      }, 10000);
    },
  };

  /* ========== 暴露到全局 ========== */

  root.Examiner = Examiner;

})(window);
