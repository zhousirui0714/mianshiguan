import yaml
import os

class ScenarioManager:
    def __init__(self, config_path='config/scenario_config.yaml'):
        self.config_path = config_path
        self.scenarios = self._load_config()
    
    def _load_config(self):
        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f)
                return config.get('scenario_themes', {})
        except Exception as e:
            print(f"Error loading config: {e}")
            return {}
    
    def get_all_scenarios(self):
        return list(self.scenarios.values())
    
    def get_scenario(self, scenario_id):
        return self.scenarios.get(scenario_id)
    
    def get_scenarios_by_category(self, category):
        return [s for s in self.scenarios.values() if s.get('category') == category]
    
    def get_categories(self):
        categories = set()
        for scenario in self.scenarios.values():
            categories.add(scenario.get('category'))
        return sorted(list(categories))

# Mock数据生成
class MockDataGenerator:
    @staticmethod
    def generate_practice_report(scenario_id):
        scenario_manager = ScenarioManager()
        scenario = scenario_manager.get_scenario(scenario_id)
        
        reports = {
            'job_interview': {
                'overall_score': 85,
                'dimensions': [
                    {'name': '技术能力', 'score': 90, 'max': 100},
                    {'name': '沟通表达', 'score': 80, 'max': 100},
                    {'name': '项目经验', 'score': 85, 'max': 100},
                    {'name': '应变能力', 'score': 82, 'max': 100}
                ],
                'percentile': 88,
                'suggestions': [
                    '继续加强技术深度，可以关注分布式系统相关问题',
                    '回答时可以更简洁一些，注意时间控制',
                    '建议多准备一些行为面试题的STAR案例'
                ],
                'strengths': ['技术基础扎实', '项目经验丰富', '表达清晰']
            },
            'teacher_cert': {
                'overall_score': 78,
                'dimensions': [
                    {'name': '教学设计', 'score': 85, 'max': 100},
                    {'name': '语言表达', 'score': 75, 'max': 100},
                    {'name': '课堂互动', 'score': 72, 'max': 100},
                    {'name': '板书设计', 'score': 80, 'max': 100}
                ],
                'percentile': 72,
                'suggestions': [
                    '试讲时要注意师生互动环节',
                    '语速可以适当放慢，给学生思考时间',
                    '板书设计还需要加强，注意书写规范'
                ],
                'strengths': ['教学设计完整', '教学目标明确', '教态自然']
            },
            'ielts_speaking': {
                'overall_score': 6.5,
                'dimensions': [
                    {'name': '流利度', 'score': 7, 'max': 9},
                    {'name': '词汇丰富度', 'score': 6, 'max': 9},
                    {'name': '语法准确性', 'score': 6.5, 'max': 9},
                    {'name': '发音', 'score': 6.5, 'max': 9}
                ],
                'percentile': 68,
                'suggestions': [
                    'Practice more complex sentence structures',
                    'Expand vocabulary related to common topics',
                    'Pay attention to word stress and intonation'
                ],
                'strengths': ['Good pronunciation', 'Clear expression', 'Confident delivery']
            },
            'civil_service': {
                'overall_score': 82,
                'dimensions': [
                    {'name': '综合分析', 'score': 85, 'max': 100},
                    {'name': '解决问题', 'score': 80, 'max': 100},
                    {'name': '组织协调', 'score': 78, 'max': 100},
                    {'name': '应变能力', 'score': 85, 'max': 100}
                ],
                'percentile': 85,
                'suggestions': [
                    '回答时要突出政府工作思维',
                    '注意政策理论知识的积累',
                    '加强人际沟通类题目的练习'
                ],
                'strengths': ['逻辑清晰', '分析深入', '立场坚定']
            },
            'graduate_school': {
                'overall_score': 80,
                'dimensions': [
                    {'name': '专业基础', 'score': 85, 'max': 100},
                    {'name': '科研潜力', 'score': 78, 'max': 100},
                    {'name': '英语能力', 'score': 75, 'max': 100},
                    {'name': '综合素质', 'score': 82, 'max': 100}
                ],
                'percentile': 80,
                'suggestions': [
                    '加强专业前沿知识的了解',
                    '准备更详细的科研规划',
                    '提高英语听说能力'
                ],
                'strengths': ['专业基础扎实', '学习能力强', '目标明确']
            },
            'mba_interview': {
                'overall_score': 88,
                'dimensions': [
                    {'name': '领导力', 'score': 90, 'max': 100},
                    {'name': '职业规划', 'score': 85, 'max': 100},
                    {'name': '商业思维', 'score': 88, 'max': 100},
                    {'name': '沟通能力', 'score': 86, 'max': 100}
                ],
                'percentile': 92,
                'suggestions': [
                    '可以准备更多量化的职业成就案例',
                    '深入思考短期和长期职业目标的衔接',
                    '了解目标院校的特色和优势'
                ],
                'strengths': ['职业成就突出', '目标清晰', '表达自信']
            }
        }
        
        return reports.get(scenario_id, reports['job_interview'])
    
    @staticmethod
    def generate_practice_session(scenario_id):
        scenario_manager = ScenarioManager()
        scenario = scenario_manager.get_scenario(scenario_id)
        
        stages = {
            'job_interview': ['自我介绍', '技术问题', '项目经验', '行为面试', '反问环节'],
            'teacher_cert': ['结构化问答', '试讲', '答辩'],
            'ielts_speaking': ['Part 1', 'Part 2', 'Part 3'],
            'civil_service': ['综合分析', '人际沟通', '应急应变', '组织管理'],
            'graduate_school': ['专业知识', '科研经历', '英语能力', '综合素质'],
            'mba_interview': ['自我介绍', '职业经历', '领导力', '商业案例', '职业规划']
        }
        
        questions = {
            'job_interview': [
                {'q': '请介绍一下你自己', 'type': 'behavioral'},
                {'q': '说说你最熟悉的技术栈', 'type': 'technical'},
                {'q': '介绍一个你参与的项目', 'type': 'project'},
                {'q': '你最大的优点是什么', 'type': 'behavioral'}
            ],
            'teacher_cert': [
                {'q': '你为什么想当老师？', 'type': 'structured'},
                {'q': '请开始你的试讲，内容是《春》的第二自然段', 'type': 'teaching'},
                {'q': '如何处理课堂上学生捣乱的情况？', 'type': 'qa'}
            ],
            'ielts_speaking': [
                {'q': 'Do you like reading?', 'type': 'part1'},
                {'q': 'Describe a book you enjoyed reading', 'type': 'part2'},
                {'q': 'What are the benefits of reading?', 'type': 'part3'}
            ],
            'civil_service': [
                {'q': '如何看待"放管服"改革？', 'type': 'comprehensive'},
                {'q': '你和同事有矛盾怎么办？', 'type': 'interpersonal'},
                {'q': '突发公共事件如何处理？', 'type': 'emergency'}
            ],
            'graduate_school': [
                {'q': '请介绍你的本科专业', 'type': 'academic'},
                {'q': '做过哪些科研项目？', 'type': 'research'},
                {'q': '为什么选择我们学校？', 'type': 'comprehensive'}
            ],
            'mba_interview': [
                {'q': '请介绍你的职业经历', 'type': 'career'},
                {'q': '举例说明你的领导力', 'type': 'leadership'},
                {'q': '你的短期和长期职业目标是什么？', 'type': 'plan'}
            ]
        }
        
        return {
            'scenario': scenario,
            'stages': stages.get(scenario_id, stages['job_interview']),
            'questions': questions.get(scenario_id, questions['job_interview']),
            'current_stage': 0,
            'current_question': 0
        }