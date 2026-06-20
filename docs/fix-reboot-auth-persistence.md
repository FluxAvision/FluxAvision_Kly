# 重启后授权数据丢失 — 根因分析 & 修复报告

## 问题

应用安装后，电脑重启出现以下两种严重情况之一：
1. **机器码获取不到** — 重启后无法获取机器码
2. **授权数据丢失** — 已授权的信息全没了，需要重新授权

## 根因分析

### 根因 1：`_get_machine_id()` 使用不稳定因子 `uuid.getnode()`

**文件**: `backend/config.py` → `_get_machine_id()`

```python
# 原实现（已修复）
factors = [
    platform.node(),
    platform.machine(),
    platform.processor(),
    str(uuid.getnode()),  # ← 问题！跨重启可能变化
]
```

`uuid.getnode()` 在 Windows 下通过枚举网络适配器获取 MAC 地址：
- 若系统有多个网卡（有线、无线、蓝牙、Hyper-V、Docker 虚拟网卡等），枚举顺序跨重启可能不同
- 取到的 MAC 地址可能是不同网卡的，导致同一台机器在不同次启动返回不同值
- 该值变化 → `_get_machine_id()` 返回不同哈希 → `.key` 文件解密失败 → **数据丢失**

**修复**: 替换为 `utils.generate_hardware_fingerprint()`，使用 WMI 查询（主板 UUID、BIOS 序列号、CPU ID、硬盘序列号、MAC）多因子综合，跨重启稳定。

---

### 根因 2：数据库密钥解密异常时直接删除数据库

**文件**: `backend/config.py` → `_get_or_create_db_key()` 的 `except` 块

```python
# 原实现（已修复）
except Exception:
    os.remove(KEY_FILE)      # 删除密钥文件
    os.remove(DB_PATH)       # ← 直接删除数据库！灾难性操作
    os.remove(DB_PATH + "-shm")
    os.remove(DB_PATH + "-wal")
```

任何解密失败（包括因根因1导致的机器码变化）都会：
1. 删除 `.key` 密钥文件
2. 删除 `fluxavision.db` 数据库
3. 删除 WAL/SHM 文件

**修复**:
- 备份旧文件为 `.bak.{时间戳}`（可手动恢复）
- 保留详细日志（文件路径、文件是否存在、machine_id 前16位）
- 提示用户恢复方法

---

### 根因 3：数据目录在 Program Files 下（UAC 文件虚拟化）

**严重性**: ⚠️ Windows 特有

数据目录 `DATA_DIR` = `C:\Program Files\FluxAvision\data\`

Windows UAC 文件虚拟化行为：
- 安装器以管理员权限安装程序 → 数据库创建在 `C:\Program Files\...`
- 开机自启运行时权限降低 → 写操作被 Windows 重定向到 `VirtualStore`
- 读操作可能读到真实路径，也可能读到 VirtualStore
- 两次启动写的文件可能在不同位置 → **数据"丢失"假象**
- 某些 Windows 更新或安全策略变更后，对 Program Files 的写入权限可能变化

**修复**: 打包模式(Windows)下使用 `%APPDATA%/FluxAvision/data/`
- APPDATA 始终可写，不受 UAC 虚拟化影响
- 首次运行自动从旧位置（exe同级 data/）迁移数据
- 向后兼容：仅当新位置无数据且旧位置有数据时才迁移

---

### 根因 4（次要）：配置模块 import 时序

**文件**: `backend/launcher.py`

```python
# launcher.py 中 import config
from config import LOG_FILE, DATA_DIR  # 触发 config 模块级别代码执行

# 日志在 config 之后才设置
logging.basicConfig(...)  # config 初始化中的警告/错误不会写入日志文件
```

这意味着 config.py 初始化时的错误日志可能丢失。这是已有问题，不在本次修复范围内。

## 改动文件

只改了 **1 个文件**：`backend/config.py`

| 改动 | 说明 |
|------|------|
| 新增 `import shutil` | 用于文件复制迁移 |
| 新增 `_get_old_data_dir()` | 旧目录路径检查 |
| 新增 `_has_valid_data()` | 判断目录是否有有效数据 |
| 新增 `_migrate_data_dir()` | 从旧目录迁移到新目录 |
| 新增 `_get_data_dir()` | 数据目录选择逻辑（APPDATA vs exe同级） |
| 修改 `_get_project_dir()` | 文档更新 |
| 修改 `DATA_DIR` 定义 | 改用 `_get_data_dir()` |
| 修改 `_get_machine_id()` | 用 `generate_hardware_fingerprint()` 替代 `uuid.getnode()` |
| 修改 `_get_or_create_db_key()` except 块 | 备份替代删除 |
| 新增 `os.makedirs` 后的 INFO 日志 | 记录数据库路径 |

## 验证方法

### 手动验证

1. **正常启动**：
   ```
   cd backend
   python launcher.py --console
   ```
   确认控制台输出包含"数据库路径: .../data/fluxavision.db"

2. **跨重启稳定性**：
   - 在 exe 环境下启动，授权 → 重启电脑 → 再次启动 → 确认授权信息仍在

3. **数据迁移**（从旧版升级）：
   - 安装旧版 exe，授权 → 安装新版 exe → 启动 → 确认 `%APPDATA%/FluxAvision/data/` 下有数据
   - 确认原 `C:\Program Files\FluxAvision\data\` 下的数据未被删除

4. **数据库备份**（模拟密钥失效）：
   - 手动删除 `.key` 文件 → 重启 → 确认 `data/` 下有 `.bak.{时间戳}` 备份文件
   - 确认新的空数据库已创建（非空状态可正常工作）

### 回归检查

- 系统设置（门店名称、密码等）是否保留
- 已添加的设备是否保留
- 授权（License）是否激活状态
- 客流历史数据是否完整

## 分支

`fix/reboot-auth-persistence` (从 `main` 分出)

## 交付清单

- [x] 根因分析报告 — 本文档
- [x] 修复代码 — `backend/config.py`
- [x] 验证说明 — 本文档"验证方法"章节
