# 2D 数字人考官 - 集成指南

## 文件引入

在 Jinja2 模板的 `<head>` 中添加：

```html
<link rel="stylesheet" href="{{ url_for('static', filename='css/components/digital_examiner.css') }}">
<script src="{{ url_for('static', filename='js/components/digital_examiner.js') }}"></script>
```

## HTML 容器

在模板中放置一个容器元素（放在页面右侧或底部）：

```html
<div id="examiner-container"></div>
```

## 初始化

```html
<script>
document.addEventListener('DOMContentLoaded', function () {
  Examiner.init({
    scenario: '{{ scenario_id }}',        // Flask 变量注入
    containerId: 'examiner-container',
    examinerInfo: {
      name: '张经理',                     // 可选，覆盖默认
      title: '资深技术面试官 | 10年经验',
    }
  });
});
</script>
```

## 完整示例

```html
<!DOCTYPE html>
<html lang="zh-CN">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>AI模拟面试</title>
  <link rel="stylesheet" href="{{ url_for('static', filename='css/base.css') }}">
  <link rel="stylesheet" href="{{ url_for('static', filename='css/components/digital_examiner.css') }}">
  <script src="{{ url_for('static', filename='js/components/digital_examiner.js') }}"></script>
  <style>
    body {
      background: #0F172A;  /* 深色背景匹配玻璃态效果 */
      min-height: 100vh;
      display: flex;
    }
    .main-area {
      flex: 1;
      display: flex;
      flex-direction: column;
      padding: 24px;
    }
    .chat-area {
      flex: 1;
      display: flex;
      gap: 24px;
      align-items: flex-start;
    }
    .messages-panel {
      flex: 1;
      background: rgba(30, 41, 59, 0.6);
      backdrop-filter: blur(12px);
      border-radius: 16px;
      padding: 24px;
      border: 1px solid rgba(255, 255, 255, 0.06);
      min-height: 400px;
    }
    .right-panel {
      width: min(360px, 28vw);
      flex-shrink: 0;
    }
    @media (max-width: 768px) {
      .chat-area { flex-direction: column; }
      .right-panel { width: 100%; }
    }
  </style>
</head>
<body>
  <div class="main-area">
    <h1 style="color:#F1F5F9; margin-bottom:24px;">{{ scenario.name }} - 模拟面试</h1>
    <div class="chat-area">
      <div class="messages-panel">
        <!-- 对话消息区域 -->
      </div>
      <div class="right-panel">
        <div id="examiner-container"></div>
      </div>
    </div>
  </div>

  <script>
    document.addEventListener('DOMContentLoaded', function () {
      // 初始化考官
      Examiner.init({
        scenario: '{{ scenario_id }}',
        containerId: 'examiner-container',
        examinerInfo: {
          name: '{{ examiner_name }}',
          title: '{{ examiner_title }}',
        }
      });

      // --- 以下为对话流程示例 ---
      const chatMessages = document.querySelector('.messages-panel');

      // 面试开始时微笑问候
      Examiner.setExpression('smile');

      // 用户正在回答时 → 思考
      // Examiner.setExpression('thinking');

      // 用户卡壳时 → 鼓励
      // Examiner.setExpression('encouraging');

      // AI 回复时 → 微笑倾听 + 说话动效
      // Examiner.startSpeaking();
      // ... 回复结束后
      // Examiner.stopSpeaking();

      // 根据 AI 情感标签自动切换
      // Examiner.setEmotion('happy');   // → smile
      // Examiner.setEmotion('thinking');// → thinking

      // 面试结束
      // Examiner.setExpression('ending');
    });
  </script>
</body>
</html>
```

## API 参考

### Examiner.init(opts)
初始化考官组件。
- `opts.scenario` — 场景ID，决定考官外观
- `opts.containerId` — 容器 DOM id
- `opts.examinerInfo` — 可选，{ name, title }

### Examiner.setExpression(expr)
切换表情。
- `'neutral'` — 中性（默认）
- `'smile'` — 微笑
- `'thinking'` — 思考
- `'encouraging'` — 鼓励
- `'ending'` — 结束

### Examiner.startSpeaking()
开始说话动效（显示音波动画 + 加快呼吸频率）。

### Examiner.stopSpeaking()
停止说话动效。

### Examiner.setEmotion(emotion)
根据 AI 情绪标签自动切换表情。
- `'neutral'` → neutral
- `'happy'` / `'approving'` → smile
- `'thinking'` / `'confused'` → thinking
- `'encouraging'` → encouraging
- `'goodbye'` → ending

### Examiner.destroy()
销毁组件，清除定时器。

## 与现有 Chat 页面集成（examiner_chat.html）

如果要在现在的考官对话页面中使用本组件替代 Canvas 模式：

1. 在 `<head>` 中加入 CSS 和 JS
2. 将 `<div class="examiner-panel">` 中的内容替换为：
   ```html
   <div id="examiner-container"></div>
   ```
3. 删除 `live2d-examiner.js` 的加载和 `DigitalExaminer` 相关代码
4. 在 `startInterview()` → `Examiner.setExpression('smile')`
5. 在 `sendMessage()` → `Examiner.setExpression('thinking')`
6. AI 返回时 → `Examiner.startSpeaking()` → 回复完成 → `Examiner.stopSpeaking()`
7. 根据 AI 回复情感 → `Examiner.setEmotion(emotion)`
8. 面试结束 → `Examiner.setExpression('ending')`

## 立绘准备

参考 `static/images/examiners/README.md` 中的设计规范准备立绘图片。

**如果没有立绘图片，组件会自动使用 CSS 绘制的占位考官**，可直接用于开发和测试。
