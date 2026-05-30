# 2D 数字人考官 - 立绘设计规范

## 文件位置

```
static/images/examiners/
├── examiner_job_neutral.png       # 求职面试 - 中性
├── examiner_job_smile.png         # 求职面试 - 微笑
├── examiner_job_thinking.png      # 求职面试 - 思考
├── examiner_job_encouraging.png   # 求职面试 - 鼓励
├── examiner_job_ending.png        # 求职面试 - 结束
├── examiner_teaching_neutral.png  # 教资面试
├── examiner_teaching_smile.png
├── examiner_teaching_thinking.png
├── examiner_teaching_encouraging.png
├── examiner_teaching_ending.png
├── examiner_ielts_neutral.png     # 雅思口语
├── ... (同上面 5 表情)
├── examiner_civil_neutral.png     # 公务员面试
├── ... (同上面 5 表情)
├── examiner_graduate_neutral.png  # 考研复试
├── ... (同上面 5 表情)
└── examiner_mba_neutral.png       # MBA 面试
└── ... (同上面 5 表情)
```

## 命名规则

```
examiner_{场景缩写}_{表情}.png
```

| 场景ID            | 缩写       |
|-------------------|-----------|
| job_interview     | job       |
| teacher_cert      | teaching  |
| ielts_speaking    | ielts     |
| civil_service     | civil     |
| graduate_school   | graduate  |
| mba_interview     | mba       |

| 性别     | 文件名后缀 |
|---------|-----------|
| 男性    | male      |
| 女性    | female    |

| 表情         | 文件名后缀     |
|-------------|--------------|
| neutral     | neutral      |
| smile       | smile        |
| thinking    | thinking     |
| encouraging | encouraging  |
| ending      | ending       |

## 完整文件名示例

```
examiner_job_male_neutral.png     # 求职面试 - 男性 - 中性
examiner_job_male_smile.png       # 求职面试 - 男性 - 微笑
examiner_job_male_thinking.png    # 求职面试 - 男性 - 思考
examiner_job_male_encouraging.png # 求职面试 - 男性 - 鼓励
examiner_job_male_ending.png      # 求职面试 - 男性 - 结束
examiner_job_female_neutral.png   # 求职面试 - 女性 - 中性（可选）
examiner_teaching_female_neutral.png  # 教资面试 - 女性 - 中性
examiner_ielts_male_neutral.png       # 雅思口语 - 男性 - 中性
```

## 图片规格

- **尺寸**: 400 x 600 px（宽 x 高）
- **格式**: PNG（透明背景）
- **朝向**: 人物正面或微侧脸
- **构图**: 全身或半身（至少到腰部以下）
- **画布**: 居中摆放，上下留白约 5%

## 考官形象建议

| 场景ID         | 人物风格                | 服装         | 表情差异                           |
|---------------|------------------------|-------------|-----------------------------------|
| job_interview | 30-40 岁职场人士        | 商务正装     | smile 微笑亲切，thinking 微微皱眉     |
| teacher_cert  | 40-50 岁教师，温和亲切   | 职业休闲装   | smile 温和慈祥，encouraging 点头鼓励 |
| ielts_speaking| 30-40 岁外籍考官        | 商务休闲     | smile 露齿笑，thinking 侧耳倾听状     |
| civil_service | 40-50 岁严肃考官        | 深色正装     | smile 仅嘴角微扬，neutral 面无表情    |
| graduate_school| 50-60 岁教授           | 学术休闲     | smile 儒雅微笑，thinking 推眼镜动作   |
| mba_interview  | 35-45 岁商业精英       | 精致西装     | smile 自信微笑，ending 点头致意     |

## 素材来源

推荐日本免费插画网站：
1. **irasutya.com** (https://irasutya.com/) 或镜像站 **irasutoya.com**
   - 搜索 `ビジネス 男性` / `ビジネス 女性` / `面接` / `教師` / `外国人`
2. 下载后使用 **remove.bg** (https://www.remove.bg/) 去背景
3. 裁剪为 400x600 统一尺寸

## 注意事项

- 所有图片必须为统一尺寸，否则会变形
- 表情之间人物外观应一致（同一角色），避免跳跃感
- thinking 表情可搭配"偏头/侧耳"视觉元素
- 如果暂无立绘图片，组件会自动显示 CSS 绘制的占位考官
