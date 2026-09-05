# Hybrid Mount Keep APEX

本项目基于上游 [Hybrid-Mount/meta-hybrid_mount](https://github.com/Hybrid-Mount/meta-hybrid_mount) 自动构建，并恢复 Hybrid Mount 对 `/apex` 的挂载管理能力。

本仓库**不维护长期分叉的完整上游源码**。每当上游发布新版本后，GitHub Actions 会获取对应的官方 Release Tag，在原始源码基础上应用最小化 `/apex` 补丁，重新构建模块，发布 `-apex` 版本，并更新本仓库的 `update.json`。

## 功能

- 自动检查 Hybrid Mount 上游最新 Release
- 获取完全对应的官方 Release Tag
- 自动将 `apex` 恢复到 Hybrid Mount 受管分区
- 自动恢复安装阶段对 `apex` 分区的处理
- 必要时同步调整相关测试
- 自动将模块 `updateJson` 指向本仓库
- 使用上游项目自己的 `cargo xtask` 构建系统
- 自动发布 `vX.Y.Z-apex` 版本
- 自动维护 `update.json`
- 不需要长期 Merge / Rebase 上游源码
- 不积累传统 Fork 的分叉历史

## 与官方版本的区别

本项目原则上只保留一个行为差异：

```text
官方 Hybrid Mount
    ↓
不管理 /apex

本项目
    ↓
恢复 Hybrid Mount 对 /apex 的管理
```

例如：

```text
上游：
v6.1.4

本项目：
v6.1.4-apex
```

构建产物类似：

```text
Hybrid-Mount-6.1.4-apex-xxxx.zip
```

## 为什么需要这个项目

Hybrid Mount 在 v6.1.x 版本线中移除了 `/apex` 受管分区支持，以避免在部分 Android 环境中干扰 APEX 激活流程。

本项目面向仍然明确需要 Hybrid Mount 管理 `/apex` 的用户，主动恢复这一行为。

## ⚠️ 风险说明

`/apex` 不是普通的静态系统分区。

它由 Android 的 `apexd` 管理，并参与系统启动阶段的 APEX 激活流程。在 `/apex` 下进行额外 OverlayFS / Magic Mount 操作可能导致：

- APEX 激活异常
- `apexd-failed`
- 挂载冲突
- 系统启动失败
- 严重情况下出现循环重启

上游之所以移除 `/apex` 支持，就是因为部分环境中已经出现过这类问题，其中包括 Android 17。

请仅在明确了解并接受风险的情况下使用本项目。

建议在测试前确认设备具备可靠的 KernelSU / APatch 安全模式、模块禁用方式或其他救砖手段。

## 关于 MoveCertificate

上游 Hybrid Mount 目前可能仍然将 `MoveCertificate` 加入模块黑名单。

本项目默认只恢复：

```text
/apex
```

挂载能力，**不会自动移除 MoveCertificate 黑名单**。

因此：

```text
恢复 /apex 支持
≠
强制让 MoveCertificate 交由 Hybrid Mount 挂载
```

如需修改黑名单，应单独评估风险。

## 自动更新机制

GitHub Actions 会定期检查上游最新 Release。

```text
检查上游最新 Release
        ↓
检查本仓库是否已经发布对应 -apex 版本
        ↓
Clone 官方 Release Tag
        ↓
执行 scripts/keep-apex.py
        ↓
恢复 /apex 支持
        ↓
修改 updateJson
        ↓
以上游 Release Tag 设置版本号
        ↓
使用上游 xtask 构建
        ↓
发布 GitHub Release
        ↓
更新 main/update.json
```

每次构建都从干净的官方 Release Tag 开始。

不会从上一个自定义版本继续 Merge，因此不会随着时间不断积累自定义源码历史。

## 检查频率

默认 GitHub Actions 每 6 小时检查一次上游：

```yaml
schedule:
  - cron: "17 */6 * * *"
```

也可以在 GitHub 中手动触发：

```text
Actions
→ Sync Upstream + Restore APEX
→ Run workflow
```

## 仓库结构

```text
.
├── .github/
│   └── workflows/
│       └── sync-apex.yml
├── scripts/
│   └── keep-apex.py
├── README.md
├── README-zh.md
└── update.json
```

### `scripts/keep-apex.py`

该脚本负责：

- 将 `apex` 加回 Rust `MANAGED_PARTITIONS`
- 将 `apex` 加回 `module/metainstall.sh`
- 调整相关测试
- 修改模块自身的 `updateJson`

如果以后上游发生较大重构，导致预期的源码结构找不到，脚本会主动失败。

相比静默生成一个可能已经损坏的安装包，这种行为更安全。

## 安装

进入本仓库的 **Releases** 页面，下载最新版：

```text
Hybrid-Mount-*-apex-*.zip
```

使用支持 MetaModule 的 KernelSU / APatch 管理器安装，然后重启设备。

## 更新通道

构建过程中会将 Hybrid Mount 的：

```text
updateJson
```

修改为本仓库：

```text
https://raw.githubusercontent.com/<owner>/<repo>/main/update.json
```

因此安装本项目版本后，后续会继续收到本项目的 `-apex` 更新，而不会自动切回官方不包含 `/apex` 支持的版本。

## 版本规则

假设上游发布：

```text
v6.1.4
```

本项目发布：

```text
v6.1.4-apex
```

模块版本类似：

```text
6.1.4-apex
```

对应 `versionCode` 根据上游数字版本计算：

```text
601004
```

版本号以上游 Release Tag 为唯一真值。

## 构建

GitHub Actions 会自动安装所需构建环境，包括：

- Node.js
- pnpm
- Rust stable
- Rust nightly
- cargo-ndk
- Android SDK
- Android NDK

最终仍然调用 Hybrid Mount 上游自己的构建入口：

```bash
cargo xtask build --ci
```

因此模块打包逻辑仍由上游 Hybrid Mount 自己的 `xtask` 负责。

## 上游项目

上游项目：

https://github.com/Hybrid-Mount/meta-hybrid_mount

本项目不是 Hybrid Mount 官方项目，也不代表或隶属于上游开发者。

如果问题仅出现在本项目的 `-apex` 构建中，请优先确认是否由恢复 `/apex` 行为导致，再决定是否向上游反馈。

## License

Hybrid Mount 上游项目采用 GPL-3.0-only 许可证。

任何对上游源码的重新分发或修改都应继续遵守对应的开源许可证要求。

## 免责声明

使用本项目意味着你已经理解：

- 本项目主动恢复了上游已经移除的 `/apex` 挂载行为
- 该行为可能干扰 Android APEX 激活机制
- 在部分设备或 Android 版本中可能造成严重启动问题
- 使用者应自行准备可靠的恢复手段
