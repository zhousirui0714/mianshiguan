"""
题库解析器 — 从 Markdown 内容中提取 (question, answer) 对

支持的格式：
1. "Q/A 标题格式": ## Q: xxx  /  ## 问：xxx  → 下一段为答案
2. "编号列表格式": 1. xxx  →  缩进段落为答案
3. "定义列表格式": - **Q:** xxx
4. "表格格式":    | 题目 | 答案 |
5. "问答块格式":  > Q: xxx  > A: xxx
6. "混合格式":    自适应检测
"""

import re
from typing import List, Dict, Optional, Tuple


class QuestionParser:
    """
    多策略 Markdown 面试题解析器。
    解析结果: {question, answer, difficulty}
    """

    # 单题最小/最大字符数
    MIN_QUESTION_LEN = 8
    MAX_QUESTION_LEN = 1000
    MIN_ANSWER_LEN = 5

    def parse(self, content: str, source_name: str = "") -> List[Dict]:
        """
        主入口：用多个策略依次尝试，合并结果去重。
        """
        if not content or len(content) < 100:
            return []

        all_questions = []

        # 每篇文章可能包含多个面试题，尝试不同解析策略
        extractors = [
            self._extract_q_a_heading,
            self._extract_numbered_list,
            self._extract_definition_list,
            self._extract_table,
            self._extract_qa_block,
        ]

        for extractor in extractors:
            try:
                questions = extractor(content)
                if questions:
                    all_questions.extend(questions)
            except Exception:
                continue

        # 去重（按题目文本去重）
        seen = set()
        unique = []
        for q in all_questions:
            text = q["question"].strip()[:100]  # 前100字作为key
            if text not in seen:
                seen.add(text)
                unique.append(q)

        return unique

    # ==================== 策略 1: Q/A 标题格式 ====================

    def _extract_q_a_heading(self, content: str) -> List[Dict]:
        """
        匹配格式:
        ## Q: 什么是xxx?
        答案内容...
        ## 问：xxx
        答案内容...

        ## Answer: xxx
        ## 答：xxx
        """
        questions = []

        # 匹配 Q 标题: ## Q: / ## 问： / ## Question: / ### Q: 等
        q_pattern = re.compile(
            r'^#{1,4}\s*(?:Q[：:]\s*|Question[：:]\s*|问[：:]\s*|面试题[：:]\s*)(.+?)$',
            re.MULTILINE,
        )

        # 匹配 A 标题: ## A: / ## 答： / ## Answer:
        a_pattern = re.compile(
            r'^#{1,4}\s*(?:A[：:]\s*|Answer[：:]\s*|答[：:]\s*|参考答案[：:]\s*)(.+?)$',
            re.MULTILINE,
        )

        lines = content.split("\n")

        # 方式 A: Q 和 A 分别有标题
        q_positions = list(q_pattern.finditer(content))
        a_positions = list(a_pattern.finditer(content))

        # 将内容按行分块
        sections = self._split_by_heading(lines)

        # 提取 Q 和 A 配对
        current_q = None
        for section in sections:
            header = section["header"]
            body = section["body"]

            q_match = q_pattern.match(header) if header else None
            a_match = a_pattern.match(header) if header else None

            if q_match:
                # 如果之前有未配对的 Q，加个空答案
                if current_q:
                    questions.append(self._make_q(current_q, ""))
                current_q = q_match.group(1).strip()
            elif a_match and current_q:
                answer = body.strip() if body else a_match.group(1).strip()
                questions.append(self._make_q(current_q, answer))
                current_q = None
            elif not a_match and current_q:
                # Q 标题后直接跟内容（没有明确的 A 标题）
                if body.strip() and len(body.strip()) > self.MIN_ANSWER_LEN:
                    questions.append(self._make_q(current_q, body.strip()))
                    current_q = None

        # 如果最后还有未配对的 Q
        if current_q:
            questions.append(self._make_q(current_q, ""))

        return questions

    def _split_by_heading(self, lines: List[str]) -> List[Dict]:
        """按 markdown 标题分割内容"""
        sections = []
        current_header = ""
        current_body = []

        for line in lines:
            if re.match(r'^#{1,4}\s', line):
                if current_header or current_body:
                    sections.append({
                        "header": current_header,
                        "body": "\n".join(current_body).strip(),
                    })
                current_header = line
                current_body = []
            else:
                current_body.append(line)

        if current_header or current_body:
            sections.append({
                "header": current_header,
                "body": "\n".join(current_body).strip(),
            })

        return sections

    # ==================== 策略 2: 编号列表格式 ====================

    def _extract_numbered_list(self, content: str) -> List[Dict]:
        """
        匹配格式:
        1. 什么是xxx?
           答案内容...
        2. 什么是yyy?
           答案内容...

        和:
        1. 题目: xxx
           答案: yyy
        """
        questions = []

        # 匹配编号项：数字. 或 数字）
        pattern = re.compile(
            r'^(?:\d+[.、)．]\s*)(?:题目[：:]\s*)?(?P<q>.+)$',
            re.MULTILINE,
        )

        lines = content.split("\n")
        i = 0
        while i < len(lines):
            line = lines[i]
            line_stripped = line.strip()

            m = pattern.match(line_stripped)
            if m:
                question = m.group("q").strip()

                # 收集后续行作为答案（直到下一个编号项或标题）
                answer_lines = []
                j = i + 1
                while j < len(lines):
                    next_line = lines[j].strip()
                    if not next_line:
                        j += 1
                        continue
                    # 检查是否遇到下一个编号项
                    if re.match(r'^\d+[.、)．]\s', next_line):
                        break
                    # 检查是否遇到标题
                    if re.match(r'^#{1,4}\s', next_line):
                        break
                    answer_lines.append(lines[j])
                    j += 1

                answer = self._clean_answer("\n".join(answer_lines))
                questions.append(self._make_q(question, answer))
                i = j
            else:
                i += 1

        return questions

    # ==================== 策略 3: 定义列表格式 ====================

    def _extract_definition_list(self, content: str) -> List[Dict]:
        """
        匹配格式:
        - **Q:** 什么是xxx?
          : 答案内容...
        - **问：** xxx
          答案内容...
        * **Question:** xxx
        """
        questions = []

        # 匹配 - **Q:** / - **问：** / - **Question:** / * **Q:** 等
        pattern = re.compile(
            r'^[\*\-\+]\s+\*\*(?:Q[：:]\s*|问[：:]\s*|Question[：:]\s*|题目[：:]\s*|面试题[：:]\s*)(.+?)\*\*',
            re.MULTILINE,
        )

        # 匹配 - **A:** / - **答：** / : 答案 等
        a_prefix_pattern = re.compile(
            r'^[\*\-\+]\s+\*\*(?:A[：:]\s*|答[：:]\s*|Answer[：:]\s*|参考答案[：:]\s*)\*\*(.+)',
            re.MULTILINE,
        )

        lines = content.split("\n")
        i = 0
        while i < len(lines):
            line = lines[i].strip()
            m = pattern.match(line)
            if m:
                question = m.group(1).strip()

                # 收集后续行作为答案
                answer_lines = []
                j = i + 1
                found_answer = False
                while j < len(lines):
                    next_line = lines[j].strip()
                    if not next_line:
                        j += 1
                        continue
                    # 下一个 Q 定义
                    if re.match(r'^[\*\-\+]\s+\*\*(?:Q[：:]|问[：:]|Question[：:])', next_line):
                        break
                    # A 前缀
                    am = a_prefix_pattern.match(next_line)
                    if am:
                        found_answer = True
                        answer_lines.append(am.group(1))
                        j += 1
                        continue
                    # 冒号开头的答案 (markdown 定义列表)
                    if next_line.startswith(":") or next_line.startswith("  "):
                        answer_lines.append(next_line.lstrip(": "))
                        j += 1
                        continue
                    # 非空行且不是列表项
                    if next_line.startswith("-") or next_line.startswith("*") or next_line.startswith("+"):
                        # 不是 Q/A 前缀的列表项，理论上不是答案
                        # 但如果是简单文本列表项，加入答案
                        if not re.match(r'^[\*\-\+]\s+\*\*', next_line):
                            answer_lines.append(next_line)
                            j += 1
                            continue
                        break
                    answer_lines.append(lines[j])
                    j += 1

                answer = self._clean_answer("\n".join(answer_lines))
                questions.append(self._make_q(question, answer))
                i = j
            else:
                i += 1

        return questions

    # ==================== 策略 4: 表格格式 ====================

    def _extract_table(self, content: str) -> List[Dict]:
        """
        匹配表格格式:
        | 题目 | 答案 |
        |------|------|
        | xxx  | yyy  |
        """
        questions = []

        # 找表格块
        table_pattern = re.compile(
            r'^\|.+\|.+\|$.*?(?:\n\|.+\|.+\|$)+',
            re.MULTILINE | re.DOTALL,
        )

        tables = table_pattern.findall(content)
        for table in tables:
            rows = table.strip().split("\n")
            if len(rows) < 3:  # header + separator + at least 1 data row
                continue

            # 跳过表头行（第二行是分隔线）
            data_rows = rows[2:]

            # 检测列头
            header_cols = [c.strip() for c in rows[0].strip("|").split("|")]
            header_cols = [c.lower() for c in header_cols]

            # 找到题目列和答案列的索引
            q_col = -1
            a_col = -1
            for idx, col in enumerate(header_cols):
                if any(kw in col for kw in ["题目", "问题", "面试题", "question", "题"]):
                    q_col = idx
                elif any(kw in col for kw in ["答案", "回答", "解答", "answer", "解析", "参考"]):
                    a_col = idx

            # 找不到明确列，默认第一列是题目，第二列是答案
            if q_col == -1:
                q_col = 0
            if a_col == -1 and len(header_cols) > 1:
                a_col = 1

            for row in data_rows:
                cols = [c.strip() for c in row.strip("|").split("|")]
                if len(cols) <= max(q_col, a_col):
                    continue
                question = cols[q_col] if q_col >= 0 else ""
                answer = cols[a_col] if a_col >= 0 else ""

                # 跳过表头、分隔线、空行
                if any(kw in question.lower() for kw in ["题目", "问题", "面试题", "question"]):
                    if len(question) < 20:
                        continue
                if not question or len(question) < self.MIN_QUESTION_LEN:
                    continue

                questions.append(self._make_q(question, answer))

        return questions

    # ==================== 策略 5: 问答块格式 ====================

    def _extract_qa_block(self, content: str) -> List[Dict]:
        """
        匹配格式:
        > Q: 什么是xxx?
        > A: 答案内容...

        或:
        **Q:** 什么是xxx?
        **A:** 答案内容...
        """
        questions = []

        # 匹配 > Q: / > **Q:** 块
        lines = content.split("\n")
        i = 0
        current_q = None
        current_a_lines = []
        in_qa = False

        while i < len(lines):
            line = lines[i].strip()

            # 检测 Q 行
            q_match = re.match(r'^>\s*\*{0,2}(?:Q[：:]\s*|问[：:]\s*|Question[：:]\s*)(.*?)\*{0,2}\s*$', line)
            # 也匹配纯文本 **Q:**
            q_match2 = re.match(r'^\*{2}(?:Q[：:]\s*|问[：:]\s*)(.*?)\*{2}', line)

            if q_match and not in_qa:
                if current_q:
                    questions.append(self._make_q(current_q, self._clean_answer("\n".join(current_a_lines))))
                current_q = q_match.group(1).strip()
                current_a_lines = []
                in_qa = True
                i += 1
                continue
            elif q_match2 and not in_qa:
                if current_q:
                    questions.append(self._make_q(current_q, self._clean_answer("\n".join(current_a_lines))))
                current_q = q_match2.group(1).strip()
                current_a_lines = []
                in_qa = True
                i += 1
                continue

            if in_qa:
                # 检测 A 行
                a_match = re.match(r'^>\s*\*{0,2}(?:A[：:]\s*|答[：:]\s*|Answer[：:]\s*|参考答案[：:]\s*)(.*?)\*{0,2}\s*$', line)
                a_match2 = re.match(r'^\*{2}(?:A[：:]\s*|答[：:]\s*)(.*?)\*{2}', line)

                if a_match:
                    current_a_lines.append(a_match.group(1))
                elif a_match2:
                    current_a_lines.append(a_match2.group(1))
                elif line.startswith(">"):
                    # 继续的引用块
                    current_a_lines.append(line.lstrip("> ").strip())
                elif not line:
                    # 空行结束 Q&A
                    if current_q:
                        questions.append(self._make_q(current_q, self._clean_answer("\n".join(current_a_lines))))
                        current_q = None
                        current_a_lines = []
                        in_qa = False
                elif re.match(r'^#{1,4}\s', line):
                    if current_q:
                        questions.append(self._make_q(current_q, self._clean_answer("\n".join(current_a_lines))))
                        current_q = None
                        current_a_lines = []
                        in_qa = False
                else:
                    current_a_lines.append(line)

            i += 1

        if current_q:
            questions.append(self._make_q(current_q, self._clean_answer("\n".join(current_a_lines))))

        return questions

    # ==================== 工具方法 ====================

    def _make_q(self, question: str, answer: str) -> Dict:
        """构造标准结果"""
        # 清理
        question = self._clean_text(question)
        answer = self._clean_answer(answer)

        # 估算难度（按字符长度和复杂度）
        difficulty = self._estimate_difficulty(question, answer)

        return {
            "question": question,
            "answer": answer,
            "difficulty": difficulty,
        }

    def _clean_text(self, text: str) -> str:
        """清理题目文本"""
        # 去掉 Markdown 标记
        text = re.sub(r'\*\*(.+?)\*\*', r'\1', text)
        text = re.sub(r'`(.+?)`', r'\1', text)
        text = re.sub(r'\[(.+?)\]\(.+?\)', r'\1', text)
        # 去掉前后空格
        text = text.strip()
        # 限制长度
        if len(text) > self.MAX_QUESTION_LEN:
            text = text[:self.MAX_QUESTION_LEN]
        return text

    def _clean_answer(self, text: str) -> str:
        """清理答案文本"""
        if not text:
            return ""
        text = re.sub(r'\*\*(.+?)\*\*', r'\1', text)
        text = re.sub(r'`(.+?)`', r'\1', text)
        text = re.sub(r'\[(.+?)\]\(.+?\)', r'\1', text)
        text = re.sub(r'^>\s*', '', text, flags=re.MULTILINE)
        text = text.strip()
        if len(text) < self.MIN_ANSWER_LEN:
            return ""
        return text

    def _estimate_difficulty(self, question: str, answer: str) -> int:
        """估算题目难度 1-5"""
        score = 3  # 默认中等

        # 关键词提分
        hard_kw = ["设计", "优化", "高并发", "分布式", "源码", "原理",
                   "底层", "性能", "架构"]
        easy_kw = ["是什么", "什么是", "请介绍", "请简述", "列举"]

        for kw in hard_kw:
            if kw in question:
                score += 1
                break
        for kw in easy_kw:
            if kw in question:
                score -= 1
                break

        # 答案长度提分
        if answer:
            if len(answer) > 500:
                score += 1
            elif len(answer) < 50:
                score -= 1

        return max(1, min(5, score))
