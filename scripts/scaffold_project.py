#!/usr/bin/env python3
"""Create a non-destructive oral-history memoir project workspace."""

from __future__ import annotations

import argparse
import csv
import json
import re
import sys
from datetime import date
from pathlib import Path


DIRECTORIES = (
    "00-consent",
    "01-audio-original",
    "02-asr-original",
    "03-transcript-edited",
    "04-evidence-cards",
    "05-drafts",
    "06-qa",
    "07-production",
    "08-delivery-archive",
)


def safe_write(path: Path, content: str, force: bool) -> None:
    if path.exists() and not force:
        raise FileExistsError(f"Refusing to overwrite existing file: {path}")
    path.write_text(content, encoding="utf-8")


def write_csv(path: Path, header: list[str], force: bool) -> None:
    if path.exists() and not force:
        raise FileExistsError(f"Refusing to overwrite existing file: {path}")
    with path.open("w", encoding="utf-8-sig", newline="") as handle:
        csv.writer(handle).writerow(header)


def build_project(root: Path, project_id: str, title: str, force: bool) -> None:
    if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._-]{2,63}", project_id):
        raise ValueError("project-id must be 3-64 safe characters: letters, digits, dot, underscore, hyphen")

    root.mkdir(parents=True, exist_ok=True)
    if any(root.iterdir()) and not force:
        raise FileExistsError(f"Target directory is not empty: {root}. Use --force only after reviewing it.")
    for directory in DIRECTORIES:
        (root / directory).mkdir(exist_ok=True)

    metadata = {
        "project_id": project_id,
        "title": title,
        "created_on": date.today().isoformat(),
        "audience": "",
        "use_scope": "private_family_collection",
        "target_length": "",
        "narrator_approval_status": "pending",
        "print_approval_status": "pending",
    }
    safe_write(root / "project.json", json.dumps(metadata, ensure_ascii=False, indent=2) + "\n", force)

    safe_write(
        root / "00-consent" / "授权与范围确认.md",
        """# 授权与范围确认

项目编号：
叙述者：
客户/付款人：
服务方：
目标读者与使用范围：

## 分项确认

- [ ] 自愿参加访谈并录音
- [ ] 同意约定的本地或云端 AI 转写/整理方式
- [ ] 同意指定人员查看中间稿
- [ ] 同意使用已列明的照片和家庭资料
- [ ] 同意家庭内部印刷与赠送
- [ ] 公开出版、网络发布或营销展示另行书面授权

## 内容边界

不得询问/不得使用：
仅作背景：
需要匿名：
可随时撤回的范围和处理方法：

## 数据处理

允许使用的工具/提供商：
访问人员：
保留期限：
删除与返还方式：

叙述者确认：                日期：
客户确认：                  日期：
服务方确认：                日期：
""",
        force,
    )

    write_csv(
        root / "03-transcript-edited" / "speaker-map.csv",
        ["session_id", "auto_label", "display_name", "role", "identity_status", "reviewer", "notes"],
        force,
    )
    write_csv(
        root / "04-evidence-cards" / "fact-ledger.csv",
        [
            "fact_id", "chapter", "type", "statement", "source_file", "timecode_or_locator",
            "speaker_or_owner", "status", "sensitivity", "allowed_use", "notes",
        ],
        force,
    )
    write_csv(
        root / "06-qa" / "source-register.csv",
        ["source_id", "source_type", "file", "sha256", "owner", "permission", "received_on", "notes"],
        force,
    )
    safe_write(
        root / "06-qa" / "final-qa-checklist.md",
        """# 最终质量检查

- [ ] 叙述者批准最终正文
- [ ] 人名、日期、数字、关系和照片说明已核对
- [ ] 所有直接引语可回到来源
- [ ] 待确认/冲突/听不清事项已处理或获准概括
- [ ] 第三方隐私和敏感信息已审核
- [ ] 最终文件无 TODO、占位符、批注和修订
- [ ] 目录、页码、章节首页和图片清晰度已核对
- [ ] DOCX/PDF 已逐页渲染并检查
- [ ] 实体样书已批准
- [ ] 交付清单、留存期限和删除方式已确认
""",
        force,
    )
    safe_write(
        root / "07-production" / "print-spec.md",
        """# 印刷规格

版本号：
成品尺寸：A5（148 × 210 mm）/ 其他：
预计页数：
正文与标题字体：
正文大小与行距：
彩色/黑白：
纸张：
装订：
封面工艺：
印数：
样书批准人及日期：
印刷母版文件及校验值：
""",
        force,
    )
    safe_write(
        root / "08-delivery-archive" / "retention-plan.md",
        """# 交付、留存与删除记录

最终交付文件：
交付日期与接收人：
内部证据保留范围：
保留截止日期：
应删除的本地临时文件：
应删除的云端副本：
资料返还情况：
执行人及完成日期：
""",
        force,
    )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("output", type=Path, help="Project directory to create")
    parser.add_argument("--project-id", required=True, help="Pseudonymous project ID")
    parser.add_argument("--title", default="家庭口述回忆录", help="Working project title")
    parser.add_argument("--force", action="store_true", help="Allow overwriting generated template files")
    args = parser.parse_args()
    try:
        build_project(args.output.expanduser().resolve(), args.project_id, args.title, args.force)
    except (FileExistsError, ValueError, OSError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1
    print(f"Created oral-history memoir project: {args.output.expanduser().resolve()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
