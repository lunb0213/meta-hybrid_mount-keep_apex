#!/usr/bin/env python3

import os
import re
from pathlib import Path


def fail(message: str) -> None:
    raise SystemExit(f"[keep-apex] ERROR: {message}")


def patch_defs() -> None:
    path = Path("src/defs.rs")

    if not path.exists():
        fail("src/defs.rs not found; upstream layout may have changed")

    text = path.read_text(encoding="utf-8")

    pattern = re.compile(
        r'(pub const MANAGED_PARTITIONS:\s*&\[&str\]\s*=\s*&\[\n)'
        r'(.*?)'
        r'(\n\];)',
        re.S,
    )

    match = pattern.search(text)

    if not match:
        fail("MANAGED_PARTITIONS block not found in src/defs.rs")

    body = match.group(2)

    if '"apex"' not in body:
        vendor = '    "vendor",'

        if vendor not in body:
            fail('"vendor" entry not found in MANAGED_PARTITIONS')

        body = body.replace(
            vendor,
            vendor + '\n    "apex",',
            1,
        )

    new_block = match.group(1) + body + match.group(3)

    text = (
        text[:match.start()]
        + new_block
        + text[match.end():]
    )

    # 删除官方关于主动排除 /apex 的注释
    text = text.replace(
        "/// `/apex` is intentionally excluded because apexd owns its activation tree.\n",
        "",
    )

    # 如果当前上游仍然存在该测试，则同步调整测试逻辑
    text = text.replace(
        "fn apex_is_excluded_from_managed_partition_policy()",
        "fn apex_is_included_in_managed_partition_policy()",
    )

    text = text.replace(
        'assert!(!MANAGED_PARTITIONS.contains(&"apex"));',
        'assert!(MANAGED_PARTITIONS.contains(&"apex"));',
    )

    path.write_text(text, encoding="utf-8")


def patch_metainstall() -> None:
    path = Path("module/metainstall.sh")

    if not path.exists():
        fail(
            "module/metainstall.sh not found; "
            "upstream layout may have changed"
        )

    text = path.read_text(encoding="utf-8")

    pattern = re.compile(
        r'^MANAGED_PARTITIONS="([^"]*)"$',
        re.M,
    )

    match = pattern.search(text)

    if not match:
        fail(
            "MANAGED_PARTITIONS not found "
            "in module/metainstall.sh"
        )

    partitions = match.group(1).split()

    if "apex" not in partitions:
        try:
            vendor_index = partitions.index("vendor")
        except ValueError:
            fail(
                '"vendor" not found in '
                "metainstall MANAGED_PARTITIONS"
            )

        partitions.insert(vendor_index + 1, "apex")

    replacement = (
        'MANAGED_PARTITIONS="'
        + " ".join(partitions)
        + '"'
    )

    text = (
        text[:match.start()]
        + replacement
        + text[match.end():]
    )

    path.write_text(text, encoding="utf-8")


def patch_update_url() -> None:
    """
    将模块自己的 updateJson 从官方地址
    改为本仓库 main/update.json。
    """

    repository = os.environ.get("GITHUB_REPOSITORY")

    if not repository:
        fail("GITHUB_REPOSITORY is not set")

    path = Path("xtask/src/main.rs")

    if not path.exists():
        fail(
            "xtask/src/main.rs not found; "
            "upstream build layout may have changed"
        )

    text = path.read_text(encoding="utf-8")

    update_url = (
        "https://raw.githubusercontent.com/"
        f"{repository}/main/update.json"
    )

    pattern = re.compile(
        r'const UPDATE_JSON_URL:\s*&str\s*=\s*'
        r'\n\s*"[^"]+";'
    )

    replacement = (
        'const UPDATE_JSON_URL: &str =\n'
        f'    "{update_url}";'
    )

    new_text, count = pattern.subn(
        replacement,
        text,
        count=1,
    )

    if count != 1:
        fail(
            "UPDATE_JSON_URL definition not found; "
            "upstream xtask may have changed"
        )

    path.write_text(
        new_text,
        encoding="utf-8",
    )


def verify() -> None:
    defs = Path("src/defs.rs").read_text(
        encoding="utf-8"
    )

    install = Path(
        "module/metainstall.sh"
    ).read_text(
        encoding="utf-8"
    )

    if '"apex"' not in defs:
        fail(
            "verification failed: "
            "apex missing from defs.rs"
        )

    match = re.search(
        r'^MANAGED_PARTITIONS="([^"]*)"$',
        install,
        re.M,
    )

    if not match:
        fail(
            "verification failed: "
            "metainstall partition list missing"
        )

    if "apex" not in match.group(1).split():
        fail(
            "verification failed: "
            "apex missing from metainstall.sh"
        )

    print(
        "[keep-apex] /apex support "
        "successfully restored"
    )


def main() -> None:
    patch_defs()
    patch_metainstall()
    patch_update_url()
    verify()


if __name__ == "__main__":
    main()
