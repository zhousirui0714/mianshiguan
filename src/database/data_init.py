"""初始化徽章和救援话术数据"""

BADGES_DATA = [
    {
        "name": "首翻勇士",
        "description": "完成第1次复盘",
        "icon": "🎯",
        "rarity": "common",
        "unlock_condition": "完成第1次复盘"
    },
    {
        "name": "嘴瓢新手",
        "description": "第1次说错话复盘",
        "icon": "🙈",
        "rarity": "common",
        "unlock_condition": "第1次说错话复盘"
    },
    {
        "name": "卡壳新手",
        "description": "第1次卡壳复盘",
        "icon": "⚡",
        "rarity": "common",
        "unlock_condition": "第1次卡壳复盘"
    },
    {
        "name": "紧张新手",
        "description": "第1次紧张复盘",
        "icon": "💪",
        "rarity": "common",
        "unlock_condition": "第1次紧张复盘"
    },
    {
        "name": "嘴瓢收藏家",
        "description": "说错话复盘累计5次",
        "icon": "😎",
        "rarity": "rare",
        "unlock_condition": "说错话复盘累计5次"
    },
    {
        "name": "卡壳终结者",
        "description": "卡壳复盘累计5次",
        "icon": "🦾",
        "rarity": "rare",
        "unlock_condition": "卡壳复盘累计5次"
    },
    {
        "name": "复盘达人",
        "description": "累计复盘10次",
        "icon": "📚",
        "rarity": "rare",
        "unlock_condition": "累计复盘10次"
    },
    {
        "name": "面试不死鸟",
        "description": "同一公司复盘3次",
        "icon": "🔥",
        "rarity": "epic",
        "unlock_condition": "同一公司复盘3次"
    },
    {
        "name": "连续作战王",
        "description": "连续7天复盘",
        "icon": "⚔️",
        "rarity": "epic",
        "unlock_condition": "连续7天复盘"
    },
    {
        "name": "翻车哲学家",
        "description": "反思深度评分>9分",
        "icon": "🌟",
        "rarity": "legendary",
        "unlock_condition": "反思深度评分>9分"
    }
]

RESCUE_SCRIPTS_DATA = [
    {
        "crash_type": "wrong_words",
        "scenario": "说错公司名称",
        "script_content": "抱歉，我刚才太紧张了。其实我一直关注的是贵公司，因为贵公司在 XX 领域的...",
        "tips": "保持镇定，承认错误并给出正确答案比硬撑更能体现你的诚实和专业。",
        "usage_count": 0
    },
    {
        "crash_type": "wrong_words",
        "scenario": "说错面试官姓氏",
        "script_content": "不好意思，我有点紧张。您刚才提到的那个问题，我认为...",
        "tips": "适度的幽默可以缓解紧张气氛，但不要过度，保持专业形象。",
        "usage_count": 0
    },
    {
        "crash_type": "wrong_words",
        "scenario": "口误说错数据",
        "script_content": "抱歉，我想表达的是... 让我重新整理一下思路",
        "tips": "用简洁准确的语言纠正错误，不要纠结太久。",
        "usage_count": 0
    },
    {
        "crash_type": "stuck",
        "scenario": "突然忘词",
        "script_content": "这是个很好的问题，让我整理一下思路... 我认为可以从这几个方面来看",
        "tips": "面试官通常会理解你需要思考时间，这反而显示你对待问题的认真态度。",
        "usage_count": 0
    },
    {
        "crash_type": "stuck",
        "scenario": "被问住",
        "script_content": "这个问题我目前了解不够深入，但我的理解是... 面试后我会进一步学习",
        "tips": "使用结构化框架（STAR、PREP等）可以帮助你组织思路，避免卡壳。",
        "usage_count": 0
    },
    {
        "crash_type": "stuck",
        "scenario": "大脑空白",
        "script_content": "不好意思，我有点紧张。可以给我几秒钟整理一下吗？",
        "tips": "深呼吸，微笑，让自己冷静下来。",
        "usage_count": 0
    },
    {
        "crash_type": "cant_answer",
        "scenario": "技术盲区",
        "script_content": "这个技术我还没有实际使用过，但我知道它是用来... 类似的技术我用过 XX",
        "tips": "诚实比编造答案更好，展示你的学习能力和求知欲。",
        "usage_count": 0
    },
    {
        "crash_type": "cant_answer",
        "scenario": "经验不足",
        "script_content": "我目前还没有遇到过这种情况，但如果是我的话，我会先...",
        "tips": "巧妙地将话题引向你擅长的领域，但不要显得刻意。",
        "usage_count": 0
    },
    {
        "crash_type": "cant_answer",
        "scenario": "完全不会",
        "script_content": "这个领域我接触较少，不过我对相关的 XX 领域有一些了解...",
        "tips": "展示你的学习态度和逻辑思维能力。",
        "usage_count": 0
    },
    {
        "crash_type": "nervous",
        "scenario": "过度紧张",
        "script_content": "（先微笑并深呼吸）感谢您的提问，我来分享一下我的看法...",
        "tips": "面试前练习深呼吸技巧，保持自信的微笑。",
        "usage_count": 0
    },
    {
        "crash_type": "nervous",
        "scenario": "手抖声音颤",
        "script_content": "让我用一个清晰的框架来回答这个问题：首先...其次...最后总结...",
        "tips": "使用结构化回答可以让你更有条理，减少紧张感。",
        "usage_count": 0
    }
]

ACTION_SUGGESTIONS = {
    "wrong_words": [
        "下次面试前，对着镜子练习自我介绍3遍，录音回听检查",
        "准备3个万能过渡句，应对突然紧张说错话的情况",
        "把容易说错的专业术语写在卡片上，每天读一遍"
    ],
    "stuck": [
        "准备5个'争取思考时间'的话术，如'这是个很好的问题...'",
        "用STAR法则重新梳理你的项目经历，形成答题框架",
        "找一个朋友模拟面试，专门练习卡壳后的应对"
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

QUIZ_QUESTIONS = [
    {
        "id": "q1",
        "question": "当时是什么情况让你觉得'翻车'了？",
        "type": "text",
        "related_badge_clue": "crash_type_identification"
    },
    {
        "id": "q2",
        "question": "如果用1-10分评价紧张程度，你打几分？",
        "type": "rating",
        "related_badge_clue": "nervous_badge"
    },
    {
        "id": "q3",
        "question": "这件事如果重新来一次，你会怎么做？",
        "type": "text",
        "related_badge_clue": "reflection_depth"
    },
    {
        "id": "q4",
        "question": "面试官当时的反应是？",
        "type": "text",
        "related_badge_clue": "scenario_refinement"
    },
    {
        "id": "q5",
        "question": "从这个经历中你学到了什么？",
        "type": "text",
        "related_badge_clue": "growth_badge"
    }
]

BADGE_MODIFIERS = {
    "wrong_words": ["嘴瓢", "口误", "说错话"],
    "stuck": ["卡壳", "卡住", "忘词"],
    "cant_answer": ["知识盲区", "不会答", "答不上"],
    "nervous": ["紧张", "慌了", "手抖"]
}

BADGE_SUFFIXES = ["收藏家", "终结者", "克服者", "幸存者", "达人"]