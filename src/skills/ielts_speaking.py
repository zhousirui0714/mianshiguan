"""雅思口语 Skill — Part 1/2/3 完整流程"""

import random
from typing import List, Dict, Any, Optional

from src.skills.base import LLMBasedSkill
from src.core.skill.types import SkillConfig, SkillSession, AnswerRecord


class IeltsSpeakingSkill(LLMBasedSkill):
    """雅思口语 Skill — 按 Part 1/2/3 流程进行

    流程：
      Part 1 (rounds 0-4):  日常话题问答（4-5 个问题）
      Part 2 (rounds 5-6):  Cue Card 个人陈述（准备 1 分钟 + 说 2 分钟）
      Part 3 (rounds 7-10): 深度讨论（3-4 个问题）

    评分维度：流利度、词汇、语法、发音（各 9 分）
    """

    PART1_TOPICS = [
        "work or study", "hometown", "accommodation", "family",
        "hobbies", "travel", "food", "music", "reading", "sports",
        "weather", "friends", "technology", "shopping", "movies",
    ]

    PART2_CUE_CARDS = [
        {
            "topic": "Describe a person you admire.",
            "prompt": "You should say:\n- who this person is\n- how you know them\n- what they are like\nand explain why you admire them."
        },
        {
            "topic": "Describe a place you have visited that you liked.",
            "prompt": "You should say:\n- where it is\n- when you went there\n- what you did there\nand explain why you liked it."
        },
        {
            "topic": "Describe a skill you want to learn.",
            "prompt": "You should say:\n- what skill it is\n- why you want to learn it\n- how you plan to learn it\nand explain how it will benefit you."
        },
        {
            "topic": "Describe a memorable event in your life.",
            "prompt": "You should say:\n- what the event was\n- when and where it happened\n- who was with you\nand explain why it was memorable."
        },
        {
            "topic": "Describe a piece of technology you find useful.",
            "prompt": "You should say:\n- what it is\n- how you use it\n- why you find it useful\nand explain how it has changed your life."
        },
        {
            "topic": "Describe a book you have read.",
            "prompt": "You should say:\n- what book it is\n- when you read it\n- what it is about\nand explain why you liked it."
        },
        {
            "topic": "Describe a goal you have set for yourself.",
            "prompt": "You should say:\n- what the goal is\n- why you set it\n- how you plan to achieve it\nand explain how achieving it will affect your life."
        },
        {
            "topic": "Describe a tradition in your country.",
            "prompt": "You should say:\n- what the tradition is\n- when it happens\n- how people celebrate it\nand explain why it is important."
        },
    ]

    PART3_TOPICS = {
        "technology": [
            "How has technology changed the way people communicate?",
            "What are the disadvantages of relying too much on technology?",
            "Do you think technology will replace human workers in the future?",
        ],
        "education": [
            "What is the importance of education in modern society?",
            "How has education changed in your country over the past decades?",
            "What is the role of technology in education?",
        ],
        "environment": [
            "What environmental problems are most serious in your country?",
            "What can individuals do to protect the environment?",
            "Should governments do more to tackle climate change?",
        ],
        "society": [
            "How has society changed in your country over the last 20 years?",
            "What are the benefits of living in a multicultural society?",
            "What social issues concern young people today?",
        ],
        "health": [
            "What can people do to maintain a healthy lifestyle?",
            "How has the healthcare system changed in your country?",
            "What is the relationship between mental health and physical health?",
        ],
        "culture": [
            "How important is it to preserve cultural traditions?",
            "What is the impact of globalization on local cultures?",
            "How do cultural events bring communities together?",
        ],
    }

    def __init__(self, config: SkillConfig):
        super().__init__(config)
        self._current_cue_card = None
        self._part3_topic_area = None

    # ==================== 欢迎语 ====================

    def get_welcome_message(self, session: SkillSession) -> str:
        """IELTS 专属英文欢迎语"""
        name = self.config.persona.name
        title = self.config.persona.title
        return (
            f"Good day! I'm {name}, {title}.\n\n"
            f"Welcome to the IELTS Speaking test. "
            f"The test will follow the standard format:\n"
            f"- Part 1: Introduction and general questions (4-5 minutes)\n"
            f"- Part 2: Individual long turn (3-4 minutes)\n"
            f"- Part 3: Two-way discussion (4-5 minutes)\n\n"
            f"Let's begin with Part 1. "
            f"Could you please tell me your full name and where you're from?"
        )

    # ==================== 问题生成 ====================

    def generate_question(self, session: SkillSession,
                          history: List[Dict[str, str]]) -> str:
        """按 Part 1/2/3 流程生成问题"""
        round_num = session.round
        context = session.context or {}

        # 确定当前 Part
        if round_num <= 4:
            return self._generate_part1_question(session, history)
        elif round_num <= 6:
            return self._generate_part2_question(session, history, context)
        else:
            return self._generate_part3_question(session, history, context)

    def _generate_part1_question(self, session: SkillSession,
                                  history: List[Dict[str, str]]) -> str:
        """Part 1: 日常话题（首次为自我介绍，之后用 LLM 或预设话题）"""
        if session.round == 0:
            return "Could you please tell me your full name and where you're from?"

        if session.round == 1:
            return "Are you working or studying at the moment?"

        # 后续轮次从话题池随机选，用 LLM 生成具体问题
        try:
            topic = random.choice(self.PART1_TOPICS)
            system_prompt = (
                f"You are an IELTS examiner. Ask a natural follow-up question "
                f"about the topic '{topic}' as part of Part 1 of the IELTS Speaking test. "
                f"Keep it conversational and brief. Ask only ONE question."
            )
            messages = [{"role": "system", "content": system_prompt}]
            for msg in history:
                messages.append({"role": msg["role"], "content": msg["content"]})
            messages.append({
                "role": "user",
                "content": f"Ask me a question about {topic}."
            })

            response = self.llm.examiner_chat(
                scenario_id=self.config.id,
                user_message=messages[-1]["content"],
                conversation_history=history,
                user_background=session.context.get("user_background", ""),
            )
            if response:
                # 如果 LLM 返回了包含流程控制的文本，只取问题部分
                lines = [l for l in response.split('\n') if l.strip() and not l.startswith(('Part', 'Now', 'Let'))]
                return lines[0] if lines else response
        except Exception:
            pass

        # 降级：预设问题
        fallback_questions = [
            f"Let's talk about {topic}. What do you enjoy most about it?",
            f"Tell me about your experience with {topic}.",
            f"How has {topic} changed in recent years?",
            f"Why do you think {topic} is important to people?",
            f"What role does {topic} play in your daily life?",
        ]
        return random.choice(fallback_questions)

    def _generate_part2_question(self, session: SkillSession,
                                  history: List[Dict[str, str]],
                                  context: Dict[str, Any]) -> str:
        """Part 2: Cue Card 长陈述"""
        if session.round == 5:
            # 选取 Cue Card
            card = random.choice(self.PART2_CUE_CARDS)
            self._current_cue_card = card
            session.context["cue_card"] = card
            return (
                f"Now, let's move to Part 2. I'm going to give you a topic to talk about.\n\n"
                f"{card['topic']}\n\n"
                f"{card['prompt']}\n\n"
                f"You will have one minute to prepare. Please start speaking when you are ready."
            )
        else:
            # Part 2 后续追问（用户已陈述完，追问细节）
            card = session.context.get("cue_card", {})
            topic = card.get("topic", "your topic")
            try:
                response = self.llm.examiner_chat(
                    scenario_id=self.config.id,
                    user_message=f"Follow up on my answer about {topic}. Ask one specific question to get more details.",
                    conversation_history=history,
                    user_background=session.context.get("user_background", ""),
                )
                if response:
                    lines = [l for l in response.split('\n') if l.strip() and 'Part' not in l]
                    return lines[0] if lines else response
            except Exception:
                pass
            return f"Thank you. Can you tell me more about why you chose to talk about {topic}?"

    def _generate_part3_question(self, session: SkillSession,
                                  history: List[Dict[str, str]],
                                  context: Dict[str, Any]) -> str:
        """Part 3: 深度讨论"""
        if session.round == 7:
            # 选择话题领域
            self._part3_topic_area = random.choice(list(self.PART3_TOPICS.keys()))
            session.context["part3_topic"] = self._part3_topic_area
            questions = self.PART3_TOPICS[self._part3_topic_area]
            return (
                f"Good. Now let's move to Part 3, where I'll ask you some more abstract questions "
                f"related to the topic.\n\n"
                f"{questions[0]}"
            )

        # 后续 Part 3 问题
        area = session.context.get("part3_topic", "society")
        questions = self.PART3_TOPICS.get(area, self.PART3_TOPICS["society"])
        used_count = session.round - 7  # round 7 = first part3 question
        if used_count < len(questions):
            return questions[used_count]

        # 超出预设数量，用 LLM 生成
        try:
            response = self.llm.examiner_chat(
                scenario_id=self.config.id,
                user_message=f"Ask me a Part 3 style abstract question related to {area}.",
                conversation_history=history,
                user_background=session.context.get("user_background", ""),
            )
            if response:
                lines = [l for l in response.split('\n') if l.strip() and 'Part' not in l]
                return lines[0] if lines else response
        except Exception:
            pass

        return f"What do you think are the future trends in {area}?"

    # ==================== 反馈报告 ====================

    def generate_feedback(self, session: SkillSession):
        """IELTS 专属反馈：雅思 Band Score 格式"""
        result = super().generate_feedback(session)

        # 将百分制转换为雅思 Band (0-9)
        if result.overall_score is not None:
            band = round(result.overall_score / 100 * 9, 1)
            result.overall_comment = (
                f"Estimated IELTS Band: {band}/9\n\n"
                f"{result.overall_comment}"
            )

            # 更新维度分到 Band
            for dim in (result.dimension_scores or []):
                if dim.get("score") is not None:
                    dim["score"] = round(dim["score"] / 100 * 9, 1)
                    dim["max_score"] = 9

        return result

    # ==================== System Prompt ====================

    def get_system_prompt(self, session: SkillSession) -> str:
        return (
            f"You are {self.config.persona.name}, {self.config.persona.title}.\n"
            f"Tone: {self.config.persona.tone}\n"
            f"Background: {self.config.persona.background}\n\n"
            f"Test format:\n"
            f"1. Part 1 (4-5 min): Introduction and general questions about familiar topics\n"
            f"2. Part 2 (3-4 min): Cue card topic, 1 min preparation, 1-2 min speaking\n"
            f"3. Part 3 (4-5 min): Abstract discussion related to Part 2 topic\n\n"
            f"Assessment criteria:\n"
            f"- Fluency and Coherence (25%)\n"
            f"- Lexical Resource (25%)\n"
            f"- Grammatical Range and Accuracy (25%)\n"
            f"- Pronunciation (25%)\n\n"
            f"Rules:\n"
            f"- Ask only ONE question at a time\n"
            f"- Follow the IELTS standard timing\n"
            f"- Provide brief feedback after each part\n"
            f"- At the end, give approximate band score and detailed feedback"
        )
