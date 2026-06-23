"""manastone-diag — 机器人故障诊断助手。

用法:
    manastone-diag                       进入对话，交互式诊断
    manastone-diag --help                显示本帮助
    manastone-diag -p "左膝过热，帮我诊断"  单次诊断（非交互）

提交日志:
    对话中输入日志文件路径即可，支持 tar 包和目录。
    在输入框里按 @ 键可以快速选择文件。

已加载 14 份领域技能（三层架构）：
    热管理 · 通信故障 · 步态稳定性 · 电源管理 · 传感器标定
    universal(5) → humanoid(5) → X2(5)
    覆盖全部 5 个故障大类

核心操作:
    1. 拖入或 @ 选择日志包 → 自动解压
    2. 描述故障现象 → 助手分三轮诊断（每轮等你确认）
    3. 拿到诊断报告 → 建议沉淀为新的 SKILL.md

快捷操作:
    /hotkeys           查看所有快捷键

分享你的诊断经验:
    把你积累的故障案例写成 SKILL.md，放到 ~/.manastone/skills/ 目录下。
    格式参考已有的技能文件，至少需要 name 和 description 字段。
    下次启动时助手会自动加载。
"""
import subprocess
import sys
from pathlib import Path

try:
    from runtime.constants import ENGINE_BIN
except ImportError:
    ENGINE_BIN = Path.home() / ".manastone" / "engine" / "node_modules" / ".bin" / "pi"


def _find_runtime_dir() -> Path:
    here = Path(__file__).resolve().parent
    for parent in [here] + list(here.parents):
        if (parent / ".manastone" / "SYSTEM.md").exists():
            return parent
        if (parent / ".pi" / "SYSTEM.md").exists():
            return parent
    for parent in here.parents:
        if (parent / "pyproject.toml").exists():
            return parent
    return here


def main():
    if "--help" in sys.argv or "-h" in sys.argv:
        print(__doc__.strip())
        return

    runtime_dir = _find_runtime_dir()

    system_md = (runtime_dir / ".manastone" / "SYSTEM.md")
    if not system_md.exists():
        system_md = (runtime_dir / ".pi" / "SYSTEM.md")
    if not system_md.exists():
        print("manastone-diag: 未找到 SYSTEM.md", file=sys.stderr)
        print(f"  查找路径: {runtime_dir}", file=sys.stderr)
        sys.exit(1)

    try:
        subprocess.run([str(ENGINE_BIN), *sys.argv[1:]], cwd=str(runtime_dir))
    except FileNotFoundError:
        print("manastone-diag: 未找到引擎", file=sys.stderr)
        print("  请重新运行 bootstrap/install.sh 安装", file=sys.stderr)
        sys.exit(1)
