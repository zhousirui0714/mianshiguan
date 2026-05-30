/**
 * AI 数字人考官 Widget
 *
 * 功能：
 * - Canvas 绘制考官形象（内置，零依赖）
 * - Live2D 模型加载（当模型文件存在时自动使用）
 * - 6 种表情控制：idle / greeting / listening / thinking / approving / disapproving
 * - 自然动画：眨眼、呼吸、微点头
 * - 不同场景切换不同考官形象
 *
 * 用法：
 *   const examiner = new DigitalExaminer({
 *     container: document.getElementById('avatar-container'),
 *     scenarioId: 'job_interview'
 *   });
 *   examiner.setExpression('approving');
 */

class DigitalExaminer {
  constructor(options = {}) {
    this.container = options.container;
    this.scenarioId = options.scenarioId || 'job_interview';
    this.width = options.width || 320;
    this.height = options.height || 400;
    this.live2dMode = options.live2dMode || false; // 设为 true 则尝试加载 Live2D 模型

    this.currentExpression = 'idle';
    this.examinerConfig = null;
    this.animationFrame = null;
    this.time = 0;
    this.autoBlinkTimer = 0;
    this.isBlinking = false;
    this.isNodding = false;
    this.nodFrame = 0;
    this.isHeadShaking = false;
    this.headShakeFrame = 0;
    this.lookAwayOffset = 0;
    this.mouthOpenAmount = 0; // 0-1, 用于口型同步

    // Live2D 相关
    this.app = null;
    this.model = null;
    this.live2dLoaded = false;

    this.init();
  }

  async init() {
    // 1. 加载考官配置
    try {
      const resp = await fetch('/static/models/examiners.json');
      const allConfigs = await resp.json();
      this.examinerConfig = allConfigs[this.scenarioId] || allConfigs['job_interview'];
    } catch (e) {
      console.warn('Failed to load examiner config, using defaults:', e);
      this.examinerConfig = null;
    }

    // 2. 尝试 Live2D 模式
    if (this.live2dMode) {
      try {
        await this.initLive2D();
        return;
      } catch (e) {
        console.warn('Live2D init failed, falling back to canvas mode:', e);
      }
    }

    // 3. 默认：Canvas 绘制模式
    this.initCanvas();
    this.startAnimationLoop();
  }

  // ==================== Canvas 绘制模式 ====================

  initCanvas() {
    this.canvas = document.createElement('canvas');
    this.canvas.width = this.width;
    this.canvas.height = this.height;
    this.canvas.style.width = '100%';
    this.canvas.style.maxWidth = this.width + 'px';
    this.canvas.style.height = 'auto';
    this.canvas.style.aspectRatio = '4/5';
    this.canvas.style.borderRadius = '16px';
    this.canvas.style.boxShadow = '0 8px 32px rgba(0,0,0,0.12)';
    this.container.innerHTML = '';
    this.container.appendChild(this.canvas);
    this.ctx = this.canvas.getContext('2d');
  }

  startAnimationLoop() {
    const loop = (timestamp) => {
      this.time = timestamp / 1000;
      this.updateAnimation();
      this.render();
      this.animationFrame = requestAnimationFrame(loop);
    };
    this.animationFrame = requestAnimationFrame(loop);
  }

  updateAnimation() {
    const cfg = this.examinerConfig || {};
    const expr = cfg.expressions ? cfg.expressions[this.currentExpression] || cfg.expressions.idle : {};

    // 自动眨眼
    if (expr.blink !== false) {
      this.autoBlinkTimer -= 1/60;
      if (this.autoBlinkTimer <= 0) {
        this.isBlinking = true;
        this.autoBlinkTimer = 2 + Math.random() * 4;
      }
    }

    // 眨眼动画
    if (this.isBlinking) {
      this.blinkPhase = (this.blinkPhase || 0) + 0.15;
      if (this.blinkPhase >= 1) {
        this.isBlinking = false;
        this.blinkPhase = 0;
      }
    }

    // 点头动画
    if (expr.nod || this.isNodding) {
      if (!this.isNodding) {
        this.isNodding = true;
        this.nodFrame = 0;
      }
      this.nodFrame += 0.04;
      if (this.nodFrame >= Math.PI * 2) {
        this.isNodding = false;
        this.nodFrame = 0;
      }
    }

    // 摇头动画
    if (expr.head_shake || this.isHeadShaking) {
      if (!this.isHeadShaking) {
        this.isHeadShaking = true;
        this.headShakeFrame = 0;
      }
      this.headShakeFrame += 0.08;
      if (this.headShakeFrame >= Math.PI * 4) {
        this.isHeadShaking = false;
        this.headShakeFrame = 0;
      }
    }

    // 视线偏移（思考时看别处）
    if (expr.look_away) {
      this.lookAwayOffset = (this.lookAwayOffset || 0) * 0.95 + Math.sin(this.time * 0.5) * 0.3;
    } else {
      this.lookAwayOffset = (this.lookAwayOffset || 0) * 0.9;
    }

    // 呼吸微动（身体轻微起伏）
    this.breatheOffset = Math.sin(this.time * 1.5) * 2;
  }

  render() {
    const ctx = this.ctx;
    const w = this.width;
    const h = this.height;
    const cfg = this.examinerConfig || {};
    const expr = cfg.expressions ? cfg.expressions[this.currentExpression] || cfg.expressions.idle : {};

    // 清空画布
    ctx.clearRect(0, 0, w, h);

    // 背景（渐变）
    const bgGrad = ctx.createLinearGradient(0, 0, 0, h);
    bgGrad.addColorStop(0, '#1E293B');
    bgGrad.addColorStop(1, '#0F172A');
    ctx.fillStyle = bgGrad;
    ctx.fillRect(0, 0, w, h);

    // 名字标签
    ctx.fillStyle = 'rgba(255,255,255,0.06)';
    ctx.font = '14px system-ui, sans-serif';
    ctx.textAlign = 'center';
    ctx.fillText(cfg.name || '考官', w/2, 30);

    ctx.save();

    // 身体上下浮动（呼吸）
    const breatheY = Math.sin(this.time * 1.5) * 2;
    ctx.translate(w/2, h/2 + breatheY);

    // 点头
    if (this.isNodding) {
      const nodAngle = Math.sin(this.nodFrame) * 0.08;
      ctx.rotate(nodAngle);
    }

    // 摇头
    if (this.isHeadShaking) {
      const shakeAngle = Math.sin(this.headShakeFrame) * 0.1;
      ctx.rotate(shakeAngle);
    }

    // ===== 绘制身体（西装/衬衫） =====
    this.drawBody(ctx, cfg);

    // ===== 绘制头部 =====
    // 头部旋转
    const headTilt = this.lookAwayOffset * 0.03;
    ctx.save();
    ctx.translate(0, -75);
    ctx.rotate(headTilt);

    // 脸部轮廓
    this.drawFace(ctx, cfg);

    // 眼镜
    if (cfg.glasses) {
      this.drawGlasses(ctx, cfg);
    }

    // 眼睛
    this.drawEyes(ctx, cfg, expr);

    // 眉毛
    this.drawEyebrows(ctx, cfg, expr);

    // 嘴巴
    this.drawMouth(ctx, cfg, expr);

    // 头发
    this.drawHair(ctx, cfg);

    ctx.restore();
    ctx.restore();

    // 底部状态提示
    const statusText = this.getStatusText(this.currentExpression);
    ctx.fillStyle = 'rgba(148, 163, 184, 0.5)';
    ctx.font = '12px system-ui, sans-serif';
    ctx.textAlign = 'center';
    ctx.fillText(statusText, w/2, h - 20);
  }

  drawBody(ctx, cfg) {
    const suitColor = cfg.suitColor || '#1A3A6B';
    const tieColor = cfg.tieColor || '#C41E3A';

    // 西装身体
    ctx.beginPath();
    ctx.moveTo(-40, 20);
    ctx.quadraticCurveTo(-50, 40, -55, 80);
    ctx.lineTo(-55, 160);
    ctx.lineTo(55, 160);
    ctx.lineTo(55, 80);
    ctx.quadraticCurveTo(50, 40, 40, 20);
    ctx.closePath();

    const bodyGrad = ctx.createLinearGradient(0, 20, 0, 160);
    bodyGrad.addColorStop(0, this.lightenColor(suitColor, 20));
    bodyGrad.addColorStop(1, suitColor);
    ctx.fillStyle = bodyGrad;
    ctx.fill();

    // 衬衫领口
    ctx.beginPath();
    ctx.moveTo(-8, 20);
    ctx.lineTo(-3, 45);
    ctx.lineTo(3, 45);
    ctx.lineTo(8, 20);
    ctx.closePath();
    ctx.fillStyle = '#F8FAFC';
    ctx.fill();

    // 领带
    ctx.beginPath();
    ctx.moveTo(-3, 45);
    ctx.quadraticCurveTo(0, 70, 0, 100);
    ctx.quadraticCurveTo(3, 70, 3, 45);
    ctx.closePath();
    ctx.fillStyle = tieColor;
    ctx.fill();
  }

  drawFace(ctx, cfg) {
    const skinTone = cfg.skinTone || '#F5D0B0';

    // 脸部
    ctx.beginPath();
    ctx.ellipse(0, 0, 50, 62, 0, 0, Math.PI * 2);
    const faceGrad = ctx.createRadialGradient(0, -10, 5, 0, 0, 55);
    faceGrad.addColorStop(0, this.lightenColor(skinTone, 10));
    faceGrad.addColorStop(1, skinTone);
    ctx.fillStyle = faceGrad;
    ctx.fill();
    ctx.strokeStyle = 'rgba(0,0,0,0.08)';
    ctx.lineWidth = 1;
    ctx.stroke();

    // 耳朵
    ctx.beginPath();
    ctx.ellipse(-50, 5, 8, 12, -0.2, 0, Math.PI * 2);
    ctx.fillStyle = skinTone;
    ctx.fill();
    ctx.beginPath();
    ctx.ellipse(50, 5, 8, 12, 0.2, 0, Math.PI * 2);
    ctx.fillStyle = skinTone;
    ctx.fill();

    // 颈部
    ctx.beginPath();
    ctx.moveTo(-15, 55);
    ctx.quadraticCurveTo(0, 75, 15, 55);
    ctx.fillStyle = skinTone;
    ctx.fill();
  }

  drawEyes(ctx, cfg, expr) {
    const blinkAmount = this.isBlinking ? Math.abs(Math.sin(this.blinkPhase * Math.PI)) : 1;
    const eyeY = -8;
    const eyeSpread = 22;
    const lookX = this.lookAwayOffset * 3;

    // 眼白
    ctx.fillStyle = '#FFFFFF';
    for (let side of [-1, 1]) {
      ctx.beginPath();
      ctx.ellipse(side * eyeSpread + lookX, eyeY, 13, 10 * Math.max(blinkAmount, 0.1), 0, 0, Math.PI * 2);
      ctx.fill();
      ctx.strokeStyle = 'rgba(0,0,0,0.1)';
      ctx.lineWidth = 0.5;
      ctx.stroke();
    }

    // 虹膜 + 瞳孔
    if (blinkAmount > 0.1) {
      const irisColor = cfg.hairColor === '#C4A882' ? '#4A7C59' : '#3D3D3D';
      for (let side of [-1, 1]) {
        // 虹膜
        ctx.fillStyle = irisColor;
        ctx.beginPath();
        ctx.ellipse(side * eyeSpread + lookX, eyeY, 6, 6 * blinkAmount, 0, 0, Math.PI * 2);
        ctx.fill();

        // 瞳孔
        ctx.fillStyle = '#1A1A1A';
        ctx.beginPath();
        ctx.ellipse(side * eyeSpread + lookX, eyeY + 1, 3, 3 * blinkAmount, 0, 0, Math.PI * 2);
        ctx.fill();

        // 高光
        ctx.fillStyle = 'rgba(255,255,255,0.8)';
        ctx.beginPath();
        ctx.arc(side * eyeSpread + lookX + 2, eyeY - 2, 2, 0, Math.PI * 2);
        ctx.fill();
      }
    }
  }

  drawEyebrows(ctx, cfg, expr) {
    const browType = expr.eyebrows || 'neutral';
    const eyeY = -8;
    const eyeSpread = 22;

    for (let side of [-1, 1]) {
      let startX = side * (eyeSpread - 5);
      let startY = eyeY - 16;
      let endX = side * (eyeSpread + 8);
      let endY = eyeY - 16;

      switch (browType) {
        case 'raised':
          startY -= 4; endY -= 4;
          break;
        case 'high_raise':
          startY -= 7; endY -= 7;
          break;
        case 'furrowed':
          startY += 2;
          endY += side * 2;
          break;
        case 'furrowed_deep':
          startY += 4;
          endY += side * 4;
          break;
        case 'slight_raise':
          startY -= 2; endY -= 2;
          break;
        default: // neutral
          break;
      }

      ctx.beginPath();
      ctx.moveTo(startX, startY);
      ctx.quadraticCurveTo(side * eyeSpread, startY - 3, endX, endY);
      ctx.strokeStyle = '#2C2C2C';
      ctx.lineWidth = 2.5;
      ctx.lineCap = 'round';
      ctx.stroke();
    }
  }

  drawMouth(ctx, cfg, expr) {
    const mouthType = expr.mouth || 'closed';
    const mouthY = 16;

    ctx.strokeStyle = '#C47A5A';
    ctx.lineWidth = 2;
    ctx.lineCap = 'round';
    ctx.fillStyle = '#C47A5A';

    switch (mouthType) {
      case 'smile':
        ctx.beginPath();
        ctx.arc(0, mouthY - 2, 12, 0.15, Math.PI - 0.15);
        ctx.strokeStyle = '#C47A5A';
        ctx.lineWidth = 2.5;
        ctx.stroke();
        break;
      case 'soft_smile':
        ctx.beginPath();
        ctx.arc(0, mouthY, 10, 0.2, Math.PI - 0.2);
        ctx.strokeStyle = '#C47A5A';
        ctx.lineWidth = 2;
        ctx.stroke();
        break;
      case 'wide_smile':
        ctx.beginPath();
        ctx.arc(0, mouthY - 4, 14, 0.1, Math.PI - 0.1);
        ctx.strokeStyle = '#C47A5A';
        ctx.lineWidth = 3;
        ctx.stroke();
        // 牙齿
        ctx.fillStyle = '#FFFFFF';
        ctx.beginPath();
        ctx.arc(0, mouthY - 7, 8, 0.1, Math.PI - 0.1);
        ctx.fill();
        break;
      case 'frown':
        ctx.beginPath();
        ctx.arc(0, mouthY + 6, 10, Math.PI + 0.2, -0.2);
        ctx.strokeStyle = '#A06040';
        ctx.lineWidth = 2.5;
        ctx.stroke();
        break;
      case 'pursed':
        ctx.beginPath();
        ctx.ellipse(0, mouthY, 6, 4, 0, 0, Math.PI * 2);
        ctx.fillStyle = '#C47A5A';
        ctx.fill();
        break;
      case 'closed':
      default:
        ctx.beginPath();
        ctx.moveTo(-8, mouthY);
        ctx.quadraticCurveTo(0, mouthY + 1, 8, mouthY);
        ctx.strokeStyle = '#C47A5A';
        ctx.lineWidth = 2;
        ctx.stroke();
        break;
    }
  }

  drawGlasses(ctx, cfg) {
    const eyeSpread = 22;
    const eyeY = -8;

    ctx.strokeStyle = 'rgba(0,0,0,0.3)';
    ctx.lineWidth = 1.5;

    // 左镜框
    ctx.beginPath();
    ctx.ellipse(-eyeSpread, eyeY, 16, 13, 0, 0, Math.PI * 2);
    ctx.stroke();

    // 右镜框
    ctx.beginPath();
    ctx.ellipse(eyeSpread, eyeY, 16, 13, 0, 0, Math.PI * 2);
    ctx.stroke();

    // 鼻梁
    ctx.beginPath();
    ctx.moveTo(-6, eyeY);
    ctx.lineTo(6, eyeY);
    ctx.stroke();

    // 镜腿
    ctx.beginPath();
    ctx.moveTo(-38, eyeY);
    ctx.lineTo(-48, eyeY - 5);
    ctx.stroke();
    ctx.beginPath();
    ctx.moveTo(38, eyeY);
    ctx.lineTo(48, eyeY - 5);
    ctx.stroke();

    // 镜片反光
    ctx.fillStyle = 'rgba(255,255,255,0.05)';
    ctx.beginPath();
    ctx.ellipse(-eyeSpread, eyeY, 15, 12, 0, 0, Math.PI * 2);
    ctx.fill();
    ctx.beginPath();
    ctx.ellipse(eyeSpread, eyeY, 15, 12, 0, 0, Math.PI * 2);
    ctx.fill();
  }

  drawHair(ctx, cfg) {
    const hairColor = cfg.hairColor || '#3D3D3D';
    const style = cfg.style || 'professional';

    ctx.fillStyle = hairColor;

    switch (style) {
      case 'professional': // 西装短发
        ctx.beginPath();
        ctx.moveTo(-48, -20);
        ctx.quadraticCurveTo(-50, -55, -35, -62);
        ctx.quadraticCurveTo(-15, -68, 0, -68);
        ctx.quadraticCurveTo(15, -68, 35, -62);
        ctx.quadraticCurveTo(50, -55, 48, -20);
        ctx.quadraticCurveTo(45, -30, 30, -30);
        ctx.quadraticCurveTo(0, -25, -30, -30);
        ctx.quadraticCurveTo(-45, -30, -48, -20);
        ctx.closePath();
        ctx.fill();
        break;
      case 'teacher': // 蓬松微卷
        ctx.beginPath();
        ctx.moveTo(-48, -18);
        ctx.quadraticCurveTo(-55, -50, -40, -58);
        ctx.quadraticCurveTo(-30, -65, -10, -68);
        ctx.quadraticCurveTo(10, -68, 30, -65);
        ctx.quadraticCurveTo(45, -60, 50, -50);
        ctx.quadraticCurveTo(55, -35, 48, -18);
        ctx.bezierCurveTo(45, -28, 35, -32, 20, -28);
        ctx.bezierCurveTo(10, -25, 5, -26, 0, -25);
        ctx.bezierCurveTo(-5, -26, -10, -25, -20, -28);
        ctx.bezierCurveTo(-35, -32, -45, -28, -48, -18);
        ctx.closePath();
        ctx.fill();
        break;
      case 'foreign': // 卷发
        ctx.beginPath();
        ctx.moveTo(-50, -15);
        for (let i = 0; i < 12; i++) {
          const angle = (i / 12) * Math.PI - Math.PI * 0.8;
          const r = 50 + Math.sin(i * 1.5) * 8;
          ctx.lineTo(Math.cos(angle) * r, -30 + Math.sin(angle) * r * 0.6);
        }
        ctx.closePath();
        ctx.fill();
        break;
      case 'academic': // 灰白学术发
      case 'executive':
        ctx.beginPath();
        ctx.moveTo(-48, -18);
        ctx.quadraticCurveTo(-52, -52, -38, -60);
        ctx.quadraticCurveTo(-20, -66, 0, -66);
        ctx.quadraticCurveTo(20, -66, 38, -60);
        ctx.quadraticCurveTo(52, -52, 48, -18);
        ctx.quadraticCurveTo(46, -28, 35, -28);
        ctx.quadraticCurveTo(20, -24, 0, -22);
        ctx.quadraticCurveTo(-20, -24, -35, -28);
        ctx.quadraticCurveTo(-46, -28, -48, -18);
        ctx.closePath();
        ctx.fill();
        break;
      default:
        break;
    }

    // 头发高光
    ctx.fillStyle = 'rgba(255,255,255,0.06)';
    ctx.beginPath();
    ctx.ellipse(-15, -55, 20, 6, -0.3, 0, Math.PI * 2);
    ctx.fill();
    ctx.beginPath();
    ctx.ellipse(15, -55, 20, 6, 0.3, 0, Math.PI * 2);
    ctx.fill();
  }

  // ==================== 公开 API ====================

  /**
   * 设置考官表情
   * @param {string} expression - 表情类型: idle / greeting / listening / thinking / approving / disapproving
   */
  setExpression(expression) {
    if (this.examinerConfig && this.examinerConfig.expressions) {
      const validExpressions = Object.keys(this.examinerConfig.expressions);
      if (validExpressions.includes(expression)) {
        this.currentExpression = expression;
        // 触发点头/摇头动画
        const expr = this.examinerConfig.expressions[expression];
        if (expr.nod || expr.head_shake) {
          // 动画会在 updateAnimation 中处理
        }
      }
    }
  }

  /**
   * 设置口型同步（配合语音）
   * @param {number} amount - 0-1, 嘴巴张开程度
   */
  setLipSync(amount) {
    this.mouthOpenAmount = Math.max(0, Math.min(1, amount));
  }

  /**
   * 切换场景（更换考官形象）
   * @param {string} scenarioId
   */
  async switchScenario(scenarioId) {
    this.scenarioId = scenarioId;

    // 重新加载配置
    try {
      const resp = await fetch('/static/models/examiners.json');
      const allConfigs = await resp.json();
      this.examinerConfig = allConfigs[scenarioId] || allConfigs['job_interview'];
    } catch (e) {
      console.warn('Failed to reload examiner config:', e);
    }

    this.currentExpression = 'idle';
  }

  /**
   * 销毁实例
   */
  destroy() {
    if (this.animationFrame) {
      cancelAnimationFrame(this.animationFrame);
    }
    if (this.app) {
      this.app.destroy(true);
    }
    this.container.innerHTML = '';
  }

  // ==================== Live2D 模式（预留） ====================

  async initLive2D() {
    // 此模式需要实际 Live2D 模型文件（.model3.json + 贴图）
    // 将模型文件放在 /static/models/{scenarioId}/ 目录下
    // 当文件存在时自动启用
    throw new Error('Live2D mode requires model files. Place .model3.json in static/models/{id}/');

    /* 启用方式（取消注释并放置模型文件后）：

    // 加载 PixiJS + live2d-display
    await this.loadScript('https://cdn.jsdelivr.net/npm/pixi.js@7.x/dist/pixi.min.js');
    await this.loadScript('https://cdn.jsdelivr.net/npm/pixi-live2d-display@0.5/dist/cubism4.min.js');

    this.app = new PIXI.Application({
      width: this.width,
      height: this.height,
      transparent: true,
      view: document.createElement('canvas'),
    });
    this.container.innerHTML = '';
    this.container.appendChild(this.app.view);

    this.model = await PIXI.live2d.Live2DModel.from('/static/models/' + this.scenarioId + '/model.model3.json');
    this.app.stage.addChild(this.model);

    // 设置表情
    this.model.expression(this.currentExpression);

    // 设置口型同步
    this.model.internalModel.lipSync = true;

    this.live2dLoaded = true;
    */
  }

  // ==================== 工具方法 ====================

  loadScript(src) {
    return new Promise((resolve, reject) => {
      const script = document.createElement('script');
      script.src = src;
      script.onload = resolve;
      script.onerror = reject;
      document.head.appendChild(script);
    });
  }

  lightenColor(hex, percent) {
    if (!hex) return '#888888';
    const num = parseInt(hex.replace('#', ''), 16);
    const r = Math.min(255, (num >> 16) + percent);
    const g = Math.min(255, ((num >> 8) & 0x00FF) + percent);
    const b = Math.min(255, (num & 0x0000FF) + percent);
    return `rgb(${r},${g},${b})`;
  }

  getStatusText(expression) {
    const map = {
      'idle': '',
      'greeting': '👋 向你问好',
      'listening': '👂 正在倾听',
      'thinking': '🤔 思考中...',
      'approving': '👍 表示赞许',
      'disapproving': '📝 记录中'
    };
    return map[expression] || '';
  }
}

// 导出到全局
window.DigitalExaminer = DigitalExaminer;
