"""
Skill 自动注册入口

调用 init_skills() 从 YAML 配置目录批量加载并注册所有 Skill。
新增场景只需：1) 加 YAML 配置  2) 加 Skill 实现类  3) 在 SKILL_MAP 注册
"""

import os
from src.core.skill import registry
from src.core.skill.types import SkillConfig

# Skill 实现类映射（新增场景在这里注册）
SKILL_MAP = {
    "job_interview": "src.skills.job_interview.JobInterviewSkill",
    "teacher_cert": "src.skills.teacher_cert.TeacherCertSkill",
    "ielts_speaking": "src.skills.ielts_speaking.IeltsSpeakingSkill",
    "civil_service": "src.skills.civil_service.CivilServiceSkill",
    "graduate_school": "src.skills.graduate_school.GraduateSchoolSkill",
    "mba_interview": "src.skills.mba_interview.MBAInterviewSkill",
}


def init_skills(config_dir: str = None) -> int:
    """
    初始化所有 Skill

    Args:
        config_dir: YAML 配置目录，默认 config/skills/

    Returns:
        成功注册的 Skill 数量
    """
    if config_dir is None:
        config_dir = os.path.join(
            os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
            "config", "skills"
        )

    if not os.path.isdir(config_dir):
        print(f"[Skills] 配置目录不存在: {config_dir}")
        return 0

    import yaml

    count = 0
    for filename in sorted(os.listdir(config_dir)):
        if not filename.endswith((".yaml", ".yml")):
            continue

        filepath = os.path.join(config_dir, filename)
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                data = yaml.safe_load(f)

            if not data or not data.get("id"):
                print(f"[Skills] 跳过无效配置: {filename}")
                continue

            skill_id = data["id"]
            class_path = SKILL_MAP.get(skill_id)
            if not class_path:
                print(f"[Skills] 未找到 Skill 实现: {skill_id}（需要配置 SKILL_MAP）")
                continue

            # 动态导入 Skill 类
            module_path, class_name = class_path.rsplit(".", 1)
            module = __import__(module_path, fromlist=[class_name])
            skill_class = getattr(module, class_name)

            # 从配置构建 SkillConfig
            config = SkillConfig.from_dict(data)

            # 创建实例并注册
            skill = skill_class(config)
            registry.register(skill)
            count += 1
            print(f"[Skills] [+] 注册 {skill_id} ({data.get('name', '')})")

        except Exception as e:
            print(f"[Skills] [!] 加载 {filename} 失败: {e}")

    print(f"[Skills] 完成: 共注册 {count} 个 Skill")
    return count


# 不在模块导入时自动初始化，需在 app.py 中显式调用 init_skills()
