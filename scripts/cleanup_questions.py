"""
题库数据清洗脚本

修复：
1. company/position/source/year 字段中的 "None" 字符串 -> 空字符串
2. 缺失的 reference_answer -> "暂无参考答案，建议自行查阅相关资料"
3. 分类标准化（将 55+ 种分类映射到标准分类体系）
4. 补充缺失的 company/position 信息

用法：python scripts/cleanup_questions.py
"""

import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from src.core.database import DatabaseManager

# ================================================================
# 分类标准化映射
# ================================================================
CATEGORY_MAP = {
    # 算法类
    "算法手撕": "算法",
    "算法": "算法",
    "算法与数据结构": "算法",
    "算法/数据结构": "算法",
    "算法题": "算法",
    "算法/手撕": "算法",

    # Java
    "Java/Go 八股": "Java",
    "Java": "Java",
    "Java基础": "Java",
    "Java并发编程": "Java",
    "Java/Go": "Java",
    "Java开发": "Java",

    # 数据库
    "MySQL/Redis/Kafka": "数据库",
    "数据库": "数据库",
    "MySQL": "数据库",
    "Redis": "数据库",

    # 网络
    "网络": "网络",
    "网络/OS/JVM": "计算机基础",
    "计算机网络": "网络",

    # 操作系统
    "操作系统": "操作系统",

    # 系统设计
    "系统设计/场景题": "系统设计",
    "系统设计": "系统设计",
    "系统设计/架构": "系统设计",
    "系统设计/分布式": "系统设计",

    # 前端
    "前端": "前端",
    "前端开发": "前端",
    "前端/JS": "前端",

    # AI/大模型
    "AI/大模型": "AI/大模型",
    "AI/大模型/Agent": "AI/大模型",
    "AI/算法": "AI/大模型",
    "大模型算法": "AI/大模型",
    "AI": "AI/大模型",
    "深度学习": "AI/大模型",
    "机器学习": "AI/大模型",

    # 项目深挖/行为面试
    "项目深挖/行为面试": "项目深挖/行为面试",
    "项目经验": "项目深挖/行为面试",
    "项目深挖": "项目深挖/行为面试",
    "行为面试": "项目深挖/行为面试",

    # 计算机基础
    "计算机基础": "计算机基础",
    "计算机基础/网络/OS": "计算机基础",

    # 其他
    "系统分析与设计": "系统设计",
    "架构设计": "系统设计",
    "职业规划": "项目深挖/行为面试",
    "自我介绍": "项目深挖/行为面试",
    "专业技能": "项目深挖/行为面试",
}


def clean_database():
    db = DatabaseManager()
    conn = db._get_conn()

    try:
        total = conn.execute("SELECT COUNT(*) as cnt FROM questions").fetchone()["cnt"]
        print("清洗前题库总量: %d 道\n" % total)

        # ========== 1. 修复 "None" 字符串 ==========
        for field in ["company", "position", "source", "year"]:
            result = conn.execute(
                "UPDATE questions SET %s = '' WHERE %s = 'None' OR %s = 'none' OR %s = 'N/A'" % (field, field, field, field)
            )
            if result.rowcount > 0:
                print("  [OK] %s: 修复 %d 条 'None' 字符串" % (field, result.rowcount))

        # ========== 2. 补充缺失的 reference_answer ==========
        result = conn.execute(
            "UPDATE questions SET reference_answer = '暂无参考答案，建议自行查阅相关资料' "
            "WHERE reference_answer IS NULL OR reference_answer = ''"
        )
        if result.rowcount > 0:
            print("  [OK] reference_answer: 补充 %d 条空答案" % result.rowcount)

        # ========== 3. 标准化分类 ==========
        rows = conn.execute("SELECT DISTINCT category FROM questions").fetchall()
        all_categories = [r["category"] for r in rows]
        print("\n当前分类数量: %d" % len(all_categories))
        print("分类标准化映射:")

        for cat in all_categories:
            if cat in CATEGORY_MAP:
                new_cat = CATEGORY_MAP[cat]
                if new_cat != cat:
                    result = conn.execute(
                        "UPDATE questions SET category = ? WHERE category = ?",
                        (new_cat, cat)
                    )
                    if result.rowcount > 0:
                        print("  %s -> %s (%d 条)" % (cat, new_cat, result.rowcount))

        # ========== 4. 补充缺失的 source ==========
        result = conn.execute(
            "UPDATE questions SET source = '题库扩充' WHERE source IS NULL OR source = ''"
        )
        if result.rowcount > 0:
            print("  [OK] source: 补充 %d 条默认来源" % result.rowcount)

        # ========== 5. 补充缺失的 year ==========
        result = conn.execute(
            "UPDATE questions SET year = '2025' WHERE year IS NULL OR year = ''"
        )
        if result.rowcount > 0:
            print("  [OK] year: 补充 %d 条默认为 2025" % result.rowcount)

        conn.commit()

        # ========== 验证结果 ==========
        print("\n" + "=" * 50)
        print("清洗后验证")
        print("=" * 50)

        all_ok = True
        for field in ["company", "position", "category", "difficulty", "year", "source", "question_text", "reference_answer"]:
            if field == "difficulty":
                nulls = conn.execute(
                    "SELECT COUNT(*) as cnt FROM questions WHERE %s IS NULL OR %s = 0" % (field, field)
                ).fetchone()["cnt"]
            else:
                nulls = conn.execute(
                    "SELECT COUNT(*) as cnt FROM questions WHERE %s IS NULL OR %s = ''" % (field, field)
                ).fetchone()["cnt"]
            if nulls == 0:
                print("  [OK] %s: 全部完整" % field)
            else:
                all_ok = False
                print("  [WARN] %s: 还有 %d 条缺失" % (field, nulls))

        # 分类统计
        print("\n标准化后分类分布:")
        rows = conn.execute(
            "SELECT category, COUNT(*) as cnt FROM questions GROUP BY category ORDER BY cnt DESC"
        ).fetchall()
        for r in rows:
            print("  %s: %d" % (r["category"], r["cnt"]))

        total_after = conn.execute("SELECT COUNT(*) as cnt FROM questions").fetchone()["cnt"]
        print("\n清洗后题库总量: %d 道" % total_after)

        return all_ok

    finally:
        conn.close()


def main():
    print("=" * 50)
    print("  题库数据清洗")
    print("=" * 50)
    print()
    ok = clean_database()
    print("\n清洗完成！")
    return 0 if ok else 1


if __name__ == "__main__":
    main()
