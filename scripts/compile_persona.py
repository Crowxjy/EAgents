#!/usr/bin/env python3
"""
compile_persona.py — 把单个 persona 文件编译为完整的 System Prompt

用法:
    python3 compile_persona.py <role_id>
    python3 compile_persona.py ad-buyer-senior
    python3 compile_persona.py ad-buyer-senior --output prompt.txt
    python3 compile_persona.py ad-buyer-senior --json   # 输出结构化 json
"""
import argparse
import json
import re
import sys
from pathlib import Path

SKILL_ROOT = Path(__file__).resolve().parent.parent


def parse_frontmatter(content: str):
    """解析 YAML frontmatter,返回 (meta_dict, body_str)。
    支持:标量、内联列表、缩进列表、缩进字典。
    """
    if not content.startswith("---"):
        return {}, content
    parts = content.split("---", 2)
    if len(parts) < 3:
        return {}, content

    fm_text = parts[1].strip()
    body = parts[2].lstrip("\n")

    # 二次扫描:正确处理嵌套 dict (basic:) vs 列表 (imports:)
    meta2 = {}
    current_dict_key = None
    pending_type = None  # "dict" / "list" / None

    for raw_line in fm_text.split("\n"):
        if not raw_line.strip() or raw_line.strip().startswith("#"):
            continue

        # 缩进行 → 当前 key 的子项
        if raw_line.startswith("  ") or raw_line.startswith("\t"):
            stripped = raw_line.strip()
            if not current_dict_key:
                continue

            if stripped.startswith("- "):
                # list 项
                if pending_type != "list":
                    meta2[current_dict_key] = []
                    pending_type = "list"
                meta2[current_dict_key].append(stripped[2:].strip())
            elif ":" in stripped:
                # dict 项
                if pending_type != "dict":
                    meta2[current_dict_key] = {}
                    pending_type = "dict"
                k, v = stripped.split(":", 1)
                meta2[current_dict_key][k.strip()] = v.strip()
            continue

        # 顶级行
        if ":" in raw_line:
            key, _, value = raw_line.partition(":")
            key = key.strip()
            value = value.strip()
            current_dict_key = key
            pending_type = None

            if value == "":
                meta2[key] = None  # 等待后续缩进决定类型
            elif value.startswith("[") and value.endswith("]"):
                inner = value[1:-1].strip()
                meta2[key] = [x.strip() for x in inner.split(",")] if inner else []
            else:
                meta2[key] = value

    # 清理:无后续子项的 None → 空 list
    for k, v in list(meta2.items()):
        if v is None:
            meta2[k] = []

    return meta2, body


def load_knowledge(import_paths):
    """读取 imports 列表中的所有共享知识文件"""
    chunks = []
    for rel_path in import_paths:
        full = SKILL_ROOT / rel_path
        if not full.exists():
            chunks.append(f"<!-- 知识文件未找到: {rel_path} -->")
            continue
        with open(full, "r", encoding="utf-8") as f:
            content = f.read()
            chunks.append(f"\n### 引用知识 · {rel_path}\n\n{content}\n")
    return "\n".join(chunks)


def compile_persona(role_id: str):
    """主编译函数"""
    persona_path = SKILL_ROOT / "personas" / f"{role_id}.md"
    if not persona_path.exists():
        raise FileNotFoundError(f"角色不存在: {persona_path}")

    with open(persona_path, "r", encoding="utf-8") as f:
        content = f.read()

    meta, body = parse_frontmatter(content)

    imports = meta.get("imports", []) or []
    knowledge_text = load_knowledge(imports) if imports else ""

    system_prompt = f"""# 角色扮演任务

你现在要扮演以下角色,所有回答必须严格遵循该角色的身份、性格、知识边界、语言风格。

## 角色基本信息
- 角色 ID: {meta.get('id', role_id)}
- 角色名: {meta.get('name', '')}
- 大类: {meta.get('category', '')}
- 子类: {meta.get('sub_category', '')}
- 状态: {meta.get('status', '')}
- 版本: {meta.get('version', '')}

## 完整角色画像

{body}

## 共享知识背景(角色掌握的领域知识)
{knowledge_text}

---

## 扮演硬约束(必须遵守)

1. **第一人称代入**:用"我"自称,不暴露 AI 身份,不出现"作为 AI 助手"等话术
2. **遵守知识边界**:画像中标记为"盲区"的领域,**禁止**调用通用知识硬答,必须按"盲区反应"中的方式回应
3. **保持语言风格**:严格遵循 L4 的口头禅、表达风格、信息密度偏好
4. **触发应激反应**:遇到 L4 应激反应库中的场景,必须按预设反应输出
5. **遵循思考逻辑**:做判断/决策时按 L3 的优先序和归因路径展开
6. **使用 Few-shot 示例的语言风格**:末尾的对话片段是你的语言锚点
7. **状态为 draft 的画像**:在每次回复末尾用斜体补一句"(本角色为测试画像,保真度未验证)"

请严格按以上要求扮演。
"""
    return {
        "role_id": role_id,
        "meta": meta,
        "system_prompt": system_prompt,
        "knowledge_files": imports,
    }


def main():
    parser = argparse.ArgumentParser(description="编译 persona 为 System Prompt")
    parser.add_argument("role_id", help="角色 ID(对应 personas/<role_id>.md)")
    parser.add_argument("--output", "-o", help="输出文件路径(默认 stdout)")
    parser.add_argument("--json", action="store_true", help="以 JSON 格式输出全部信息")
    args = parser.parse_args()

    try:
        result = compile_persona(args.role_id)
    except FileNotFoundError as e:
        print(f"ERROR: {e}", file=sys.stderr)
        sys.exit(1)

    output = (
        json.dumps(result, ensure_ascii=False, indent=2)
        if args.json
        else result["system_prompt"]
    )

    if args.output:
        with open(args.output, "w", encoding="utf-8") as f:
            f.write(output)
        print(f"OK: 已写入 {args.output} ({len(output)} chars)")
    else:
        print(output)


if __name__ == "__main__":
    main()
