"""初始化徽章和救援话术数据"""

BADGES_DATA = [
    {
        "name": "初出茅庐",
        "description": "完成第一次面试复盘",
        "icon": "🎯",
        "rarity": "common",
        "unlock_condition": "完成第一次复盘"
    },
    {
        "name": "说错话大师",
        "description": "勇敢面对自己说过的错话",
        "icon": "🙈",
        "rarity": "common",
        "unlock_condition": "翻车类型为说错话"
    },
    {
        "name": "卡壳终结者",
        "description": "突破面试卡壳困境",
        "icon": "⚡",
        "rarity": "common",
        "unlock_condition": "翻车类型为卡壳"
    },
    {
        "name": "诚实勇敢",
        "description": "敢于承认自己不会答",
        "icon": "🤝",
        "rarity": "common",
        "unlock_condition": "翻车类型为不会答"
    },
    {
        "name": "抗压能手",
        "description": "从紧张中恢复的强者",
        "icon": "💪",
        "rarity": "common",
        "unlock_condition": "翻车类型为紧张发挥失常"
    },
    {
        "name": "复盘达人",
        "description": "完成5次面试复盘",
        "icon": "📚",
        "rarity": "rare",
        "unlock_condition": "完成5次复盘"
    },
    {
        "name": "面面俱到",
        "description": "解锁所有类型的翻车徽章",
        "icon": "🏆",
        "rarity": "epic",
        "unlock_condition": "解锁所有翻车类型徽章"
    },
    {
        "name": "东山再起",
        "description": "经历失败后成功拿到offer",
        "icon": "🌟",
        "rarity": "legendary",
        "unlock_condition": "标记面试成功"
    }
]

RESCUE_SCRIPTS_DATA = [
    {
        "crash_type": "wrong_words",
        "title": "说错话圆场技巧",
        "script": "非常抱歉，刚刚表述不够准确。让我重新整理一下思路...（简明扼要地纠正错误并给出正确答案）",
        "tips": "保持镇定，不要慌张。承认错误并给出正确答案比硬撑更能体现你的诚实和专业。"
    },
    {
        "crash_type": "wrong_words",
        "title": "幽默化解尴尬",
        "script": "看来我今天有点紧张，连话都不会说了。其实我想表达的是...（用轻松的语气重新表达）",
        "tips": "适度的幽默可以缓解紧张气氛，但不要过度，保持专业形象。"
    },
    {
        "crash_type": "stuck",
        "title": "请求思考时间",
        "script": "这个问题很好，让我稍微整理一下思路...（停顿3-5秒）我认为可以从以下几个方面来回答...",
        "tips": "面试官通常会理解你需要思考时间，这反而显示你对待问题的认真态度。"
    },
    {
        "crash_type": "stuck",
        "title": "结构化回答法",
        "script": "我可以从三个维度来分析这个问题：首先...其次...最后...",
        "tips": "使用结构化框架（STAR、PREP等）可以帮助你组织思路，避免卡壳。"
    },
    {
        "crash_type": "cant_answer",
        "title": "坦诚承认",
        "script": "这个问题我目前还没有深入研究过，但我可以分享一下我的理解思路...（谈谈你的学习方法）",
        "tips": "诚实比编造答案更好，展示你的学习能力和求知欲。"
    },
    {
        "crash_type": "cant_answer",
        "title": "转移话题",
        "script": "关于这个问题我了解有限，但我在相关领域有一些经验...（转向你熟悉的内容）",
        "tips": "巧妙地将话题引向你擅长的领域，但不要显得刻意。"
    },
    {
        "crash_type": "nervous",
        "title": "深呼吸放松",
        "script": "（先微笑并深呼吸）感谢您的提问，我来分享一下我的看法...",
        "tips": "面试前练习深呼吸技巧，保持自信的微笑。"
    },
    {
        "crash_type": "nervous",
        "title": "结构化思维",
        "script": "让我用一个清晰的框架来回答这个问题：首先...其次...最后总结...",
        "tips": "使用结构化回答可以让你更有条理，减少紧张感。"
    }
]

ACTION_SUGGESTIONS = {
    "wrong_words": [
        "下次面试前准备常见问题的标准答案，避免临场发挥出错",
        "练习用简洁准确的语言表达观点",
        "录制自己的回答并回放，找出表达不当的地方"
    ],
    "stuck": [
        "准备常用的回答框架（STAR、PREP等）",
        "每天练习即兴演讲，提高反应能力",
        "面试前进行模拟训练，增加自信"
    ],
    "cant_answer": [
        "针对目标岗位整理技术知识点，制作思维导图",
        "遇到不会的问题时，先表达自己的思考过程",
        "建立持续学习计划，每周学习一个新知识点"
    ],
    "nervous": [
        "面试前进行深呼吸练习和冥想",
        "准备一份自我介绍脚本，反复练习",
        "模拟真实面试环境进行训练"
    ],
    "other": [
        "回顾整个面试过程，找出需要改进的地方",
        "寻求他人的反馈和建议",
        "制定具体的改进计划并执行"
    ]
}

CRASH_TYPES = {
    "wrong_words": "说错话",
    "stuck": "卡壳",
    "cant_answer": "不会答",
    "nervous": "紧张发挥失常",
    "other": "其他"
}
