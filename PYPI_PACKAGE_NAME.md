# PyPI 包名说明

## 包名变更

由于 `miniagent` 这个名称在 PyPI 上已被占用，本项目的 PyPI 包名已变更为 **`amrita-ministudio`**。

## 安装方式

```bash
# 使用 pip 安装
pip install amrita-ministudio[full]

# 使用 uv 安装（推荐）
uv pip install amrita-ministudio[full]
```

## 使用说明

### 包名 vs 模块名 vs CLI 命令

- **PyPI 包名**：`amrita-ministudio`（用于安装）
- **Python 模块名**：`amrita`（用于导入）
- **CLI 命令**：`miniagent` 或 `amrita`（两者都可用）

### 示例

```bash
# 1. 安装包
pip install amrita-ministudio[full]

# 2. 使用 CLI 命令
miniagent --help
# 或
amrita --help

# 3. 在 Python 代码中导入
python
>>> import amrita
>>> from amrita import API
```

## 为什么这样设计？

这种设计遵循 Python 包管理的最佳实践：

1. **PyPI 包名**（`amrita-ministudio`）：
   - 在 PyPI 上全局唯一
   - 包含工作室标识（ministudio），避免与其他项目冲突
   - 使用短横线分隔符（PyPI 推荐规范）

2. **Python 模块名**（`amrita`）：
   - 代码导入路径保持简洁
   - 不需要修改现有代码
   - 使用下划线分隔符（Python 命名规范）

3. **CLI 命令**（`miniagent` / `amrita`）：
   - 保持用户习惯的命令名
   - 提供向后兼容的别名

## 相关配置

在 `pyproject.toml` 中的相关配置：

```toml
[project]
name = "amrita-ministudio"  # PyPI 包名

[project.scripts]
miniagent = "amrita.cli:main"  # CLI 命令
amrita = "amrita.cli:main"     # CLI 别名

[tool.setuptools.packages.find]
include = ["amrita", "amrita.*"]  # 实际 Python 包
```

## 发布流程

发布到 PyPI 时，`uv build` 和 `uv publish` 会自动使用 `pyproject.toml` 中的包名配置，无需额外参数。

```bash
# 构建包
uv build

# 发布到 PyPI
uv publish --token $PYPI_API_TOKEN
```

## 其他说明

- 本项目基于上游项目 [Amrita](https://github.com/LiteSuggarDEV/Amrita) 开发
- 工作室名称：ministudio
- 项目仓库：https://github.com/momo-mnsjtxy/MiniAgent
