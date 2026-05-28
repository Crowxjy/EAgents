---
name: persona-sim
description: 多角色用户模拟技能包。当用户需要以特定角色身份(广告投手/生服销售/商家/消费者等)回答问题、评判产物(PRD/设计稿/图片)、模拟用户心智操作网页时使用本 Skill。支持单角色问答、多角色圆桌评审、产物评判、网页操作模拟四种模式。每个角色画像采用 L1-L5 五层结构:身份层/标签层/心智层(思考逻辑)/行为层(做事风格)/知识层(知识库)。触发词:扮演 XX 角色、以 XX 视角、模拟 XX 用户、XX 圆桌、用户心智模拟、PRD 评审、设计稿评审。
---

# Persona Sim · 多角色用户模拟技能包

## 一、能力定位

把"用户研究 + 评审 + 心智模拟"沉淀为可复用、可工程化维护的 AI 资产。让 PM/设计师在没有真实用户的场景下,也能快速获得**贴近真人**的多视角反馈。

### 三大能力层

| 层级 | 能力 | 调用命令 |
|---|---|---|
| L1 角色化问答 | 以特定角色回答问题 | `persona ask` |
| L2 产物评判 | 多角色对 PRD/设计稿评审 | `persona review` / `persona roundtable` |
| L3 心智操作 | 以角色心智操作网页 | `persona simulate`(后续 Phase) |

## 二、触发条件

**应使用本 Skill 的场景**:
- 用户要求以某个角色/人群身份回答(如"作为广告投手,你怎么看...")
- 需要多角色评审同一产物(PRD、设计稿、文案、流程图)
- 需要模拟用户做选择、给反馈、操作页面
- 用户管理角色画像库(增删改查、查看角色列表)

**不应使用本 Skill 的场景**:
- 用户问的是通用知识(直接回答即可,无需角色化)
- 用户要求的是真实用户调研(本 Skill 是模拟,不能替代真实用研)

## 三、调用命令

```
# 列出所有角色
persona list [category]

# 单角色问答
persona ask <role_id> <question>

# 多角色圆桌(并行)
persona roundtable <role_id1,role_id2,...> <question>

# 多轮真实讨论圆桌(顺序+回应+收敛)
persona roundtable-session <role_id1,role_id2,...> --topic <topic>

# 产物评判(支持文本/图片/链接)
persona review <role_id> <artifact_path_or_url>

# 网页心智模拟(Phase 4)
persona simulate <role_id> <web_url> <task>

# 校验所有角色画像完整性
persona lint

# 用户反馈(优先表单,回退对话兜底)
persona feedback             # 等价于输出表单引导文案
persona feedback form        # 输出飞书表单 URL
persona feedback submit ...  # 兜底:把对话中收到的结构化反馈写入飞书 Base
```

## 四、目录结构

```
persona-sim-skill/
├── SKILL.md                  # 本文件
├── personas/                 # 角色画像(每角色一个 .md)
│   ├── _template.md          # 角色模板,新建角色照此填
│   └── ad-buyer-senior.md    # 已交付样板:广告投手·资深
├── knowledge/                # 共享知识库(跨角色复用)
│   ├── industry/             # 行业知识
│   ├── glossary/             # 术语词典
│   └── product/              # 产品知识
├── scenarios/                # 场景任务模板
│   ├── review-prd.md
│   ├── review-design.md
│   └── simulate-web.md
├── scripts/                  # 工程化脚本
│   ├── compile_persona.py    # 编译 persona+knowledge → SystemPrompt
│   ├── roundtable.py         # 多角色并行调用
│   └── lint.py               # 画像完整性校验
└── tests/                    # 评测集
    ├── golden/               # 标准问答对
    └── cases/                # 测试 case
```

## 五、角色画像 L1-L5 五层结构

每个角色 `.md` 文件由 YAML frontmatter(结构化)+ 正文(长文本)组成,正文按 L1-L5 五层组织:

| 层级 | 内容 | 作用 |
|---|---|---|
| **L1 身份层** | 姓名、年龄、职业、地域、履历 | 让模型有"人物画像感" |
| **L2 标签层** | 人群类别、核心痛点、核心诉求、决策风格 | 快速分类、批量筛选 |
| **L3 心智层** | 思考逻辑、决策路径、归因方式、价值观 | **决定回答深度的关键** |
| **L4 行为层** | 做事风格、工作流、沟通偏好、应激反应、口头禅 | **决定回答风格的关键** |
| **L5 知识层** | 熟练领域、半懂领域、盲区、术语体系、信息源 | **决定回答专业度的关键** |

**Few-shot 示例**:每个画像末尾必须包含 3-5 段典型对话片段,作为风格锚点。

## 六、共享知识库引用机制

在角色 frontmatter 中通过 `imports` 字段声明依赖的共享知识:

```yaml
imports:
  - knowledge/industry/ad-platform-qianchuan.md
  - knowledge/glossary/ad-terms.md
```

编译时 `compile_persona.py` 会自动将这些知识拼接进 System Prompt,实现:
- 多个广告投手共享同一份"千川后台知识"
- 改一处 → 所有相关角色生效

## 七、调用执行规范

### 7.1 角色化回答的硬要求

收到 `persona ask` / `persona review` 时,模型必须:

1. **完全代入角色**:用第一人称("我"),不暴露 AI 身份,不使用模型常用模板化句式
2. **遵守知识边界**:角色知识库未涵盖的问题,必须按角色"盲区"反应(如反问、含糊、转移话题),**禁止**调用通用知识硬答
3. **保持语言风格**:严格遵循 L4 中的"沟通偏好""口头禅""术语习惯"
4. **触发应激反应**:遇到 L4 中定义的"应激场景",必须按预设反应模式回应
5. **决策遵循 L3**:做判断时按角色的"思考逻辑""归因方式"展开,不绕过

### 7.2 圆桌评审的硬要求

收到 `persona roundtable` 时:
- 每个角色独立输出,不互相参考
- 输出格式统一:`## [角色名] · [角色类别]\n<回答正文>`
- 末尾输出"差异点对比表",由助手以中立旁白身份汇总(非角色发言)

### 7.3 产物评判的硬要求

收到 `persona review` 时:
- 评审视角必须基于该角色的**痛点 + 诉求 + 知识盲区**
- 输出结构:**直觉反应 → 具体问题点 → 角色化建议 → 整体打分(1-10)**
- 不允许给"全是优点"的评审,必须基于角色立场挑出至少 2 个问题

### 7.4 用户反馈收集的硬要求

当用户表达"反馈/报告问题/这个角色不准/这个知识有错/这里拟合不对/有 bug/有建议"等意图时,本 Skill 必须主动启动反馈收集流程,**不允许**:
- 直接修改 `personas/` 或 `knowledge/` 文件
- 仅把反馈写入用户本地的 Memory
- 假装"已记录"但没有真正提交

**收集策略(按优先级)**:

1. **首选: 飞书表单**
   - 当宿主模型/Agent 支持渲染原生表单时,优先弹出/嵌入飞书反馈表单
   - 否则向用户输出表单 URL 链接(`scripts/feedback_handler.py form-url`)
   - 表单地址: `https://bytedance.larkoffice.com/base/HGLTbRGqdagunpsf5r9cPjobnDd?table=tblEoCPkWbIc3rKk&view=vewriYNmAf`
2. **回退: 对话兜底**
   - 用户拒绝填表或环境无法跳转时,模型在对话中按字段引导用户提供以下信息:
     - 必填: `问题类型`、`问题描述`
     - 选填: `提交人`
   - 收齐后调用 `python3 scripts/feedback_handler.py submit ...` 写入飞书 Base

**兜底写入注意事项**:
- 发生写入失败时(exit code != 0),不可对用户说"已提交",必须输出错误日志并再次提供表单 URL
- 反馈记录的"处理状态"始终默认 `Todo`,由维护者后续在 Base 中流转
- 反馈记录的"反馈来源"由收集渠道决定,模型不要让用户填写

## 八、当前交付状态

| 模块 | 状态 |
|---|---|
| Skill 骨架 | ✅ 已搭建 |
| 角色模板 `_template.md` | ✅ 已交付 |
| 样板角色:广告投手·资深 | ✅ 已交付(基于真实素材) |
| 共享知识库:广告投放 | ✅ 已交付 |
| 共享知识库:广告术语词典 | ✅ 已交付 |
| 场景模板:PRD 评审 | ✅ 已交付 |
| 编译脚本 `compile_persona.py` | ✅ 已交付 |
| 圆桌脚本 `roundtable.py` | ✅ 已交付 |
| 多轮圆桌脚本 `roundtable_session.py` | ✅ 已交付 |
| 校验脚本 `lint.py` | ✅ 已交付 |
| 用户反馈收集 `feedback_handler.py` + 飞书表单 | ✅ 已交付 |
| 网页模拟能力 | ⏳ 待交付(Phase 4) |

## 九、路线图

- **Phase 1**(当前):Skill 骨架 + 1 个完整样板角色
- **Phase 2**:补齐编译/圆桌/校验脚本,跑通 L1 单角色问答 + L2 圆桌评审
- **Phase 3**:批量铺设种子角色(生服销售、商家·餐饮、商家·零售、消费者·Z 世代等)
- **Phase 4**:接入 `mira-remote-browser`,实现 L3 心智操作模拟
- **Phase 5**:评测集 + 真实用户对比 + 画像迭代
