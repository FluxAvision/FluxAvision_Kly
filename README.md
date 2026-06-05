# FluxAvision 客流统计系统

基于 **Python FastAPI + Next.js + SQLite3** 的门店客流统计与分析系统，专为大华摄像机 SDK 客流采集场景设计。

最终交付为 **Windows exe 安装包**，支持后台静默运行、开机自启、系统托盘管理。

---

## 功能特色

### 核心功能
- **大华 SDK 客流采集** —添加设备后自动登录订阅客流数据，断线指数退避重连（3s ~ 30s）
- **Ed25519 数字签名授权** —外部平台根据硬件指纹生成激活码，不可伪造、不可破解
- **AES-256 字段加密** —设备密码、登录密码、激活码等敏感字段透明加解密
- **硬件指纹绑定** —数据库密钥绑定CPU/主板/磁盘/MAC，拷贝到其他机器无法使用
- **RTSP 视频流预览** —OpenCV 拉流为 MJPEG，浏览器直接播放

### 管理功能
- 设备管理（增删改查、SDK 连接状态实时监控）
- 系统设置（门店名称、登录密码、仪表盘指标配置）
- 客流数据查询（按小时/天/设备/日期范围筛选）
- 大屏展示（自定义标题、指标、设备筛选）
- 一键生成测试数据（开发调试用）

### 打包部署
- **PyInstaller** 打包为 Windows exe（onedir 模式）
- **Inno Setup** 生成专业安装程序（桌面图标、开机自启、防火墙规则）
- 系统托盘图标（右键菜单：打开界面/退出）
- 单实例运行（重复打开自动跳转到已运行实例）

---

## 技术栈

| 层级 | 技术 | 版本 |
|------|------|------|
| 后端 | Python FastAPI | 0.135.3 |
| ORM | SQLAlchemy | 2.0.49 |
| 数据库 | SQLite3 (内置) + AES-256 字段加密 | —|
| 加密 | cryptography (AES-256-CBC) + Ed25519 | 46.0.6 |
| 视频流 | OpenCV MJPEG | 4.8+ |
| 前端 | Next.js + React 19 + TypeScript | 16.x |
| UI | shadcn/ui + Tailwind CSS | 4.x |
| 图表 | Recharts | 2.x |
| 打包 | PyInstaller + Inno Setup | 6.x |

---

## 目录结构

```
FluxAvision/
│
├── backend/                         # Python 后端
│  ├── main.py                      # FastAPI 应用入口 + 启动/关闭事件
│  ├── config.py                    # 全局配置（路径/密钥/硬件指纹）
│  ├── database.py                  # SQLite3 数据库连接 + 迁移
│  ├── field_crypto.py              # AES-256 字段加解密工具
│  ├── models.py                    # SQLAlchemy ORM 模型（含 EncryptedString 类型）
│  ├── utils.py                     # 工具函数（RTSP URL 生成/硬件指纹/响应格式）
│  │
│  ├── routers/                     # API 路由模块
│  │  ├── __init__.py              # 路由注册中心
│  │  ├── auth.py                  # POST /api/auth           —登录验证
│  │  ├── devices.py               # GET/POST /api/devices   —设备列表/创建
│  │  ├── device_id.py             # GET/PUT/DELETE /api/devices/:id —设备详情/更新/删除
│  │  ├── device_status.py         # PUT /api/devices/:id/status —设备状态
│  │  ├── traffic.py               # POST /api/traffic       —客流数据上报
│  │  ├── traffic_history.py       # GET /api/traffic/history —历史客流查询
│  │  ├── traffic_dashboard.py     # GET /api/traffic/dashboard —仪表盘聚合数据
│  │  ├── traffic_collector.py     # GET /api/traffic-collector/status —采集状态
│  │  ├── settings.py              # GET/PUT /api/settings   —系统设置
│  │  ├── license.py               # GET/POST /api/license   —授权激活
│  │  ├── seed.py                  # POST /api/seed          —生成测试数据
│  │  ├── stream.py                # GET /api/devices/:id/stream —RTSP 视频流
│  │  ├── large_screen.py          # GET/PUT /api/large-screen —大屏设置
│  │  └── large_screen_templates.py # GET /api/large-screen/templates —大屏模板
│  │
│  ├── dahua_collector.py           # 大华 SDK 客流采集核心（连接管理/订阅/重连）
│  ├── stream_manager.py            # OpenCV 视频流管理器
│  ├── license_crypto.py            # Ed25519 激活码验证模块
│  ├── windows_service.py           # Windows 服务（开机自启/单实例/托盘）
│  ├── launcher.py                  # PyInstaller 入口（命令行参数解析）
│  │
│  ├── requirements.txt             # Python 依赖
│  ├── FluxAvision.spec             # PyInstaller 打包配置
│  ├── build.bat                    # 一键构建脚本（前端+后端+打包）
│  ├── installer.iss                # Inno Setup 安装程序脚本
│  ├── create_icon.py               # 应用图标生成脚本
│  ├── build.py                     # Python 辅助构建脚本
│  ├── post_build.py                # 构建后处理脚本
│  ├── start.sh                     # Linux/macOS 启动脚本
│  │
│  └── assets/
│      └── icon.ico                 # 应用图标
│
├── src/                             # Next.js 前端源码
│  ├── app/
│  │  ├── layout.tsx               # 根布局
│  │  ├── page.tsx                 # 首页（登录页）
│  │  └── globals.css              # 全局样式
│  │
│  ├── components/
│  │  ├── auth/
│  │  │  └── LoginPage.tsx        # 登录/激活页面
│  │  ├── dashboard/
│  │  │  └── Dashboard.tsx        # 仪表盘（今日客流/趋势图）
│  │  ├── devices/
│  │  │  └── DeviceManagement.tsx # 设备管理（CRUD + 采集状态）
│  │  ├── history/
│  │  │  └── HistoryData.tsx      # 历史客流数据查询
│  │  ├── video/
│  │  │  └── RTSPVideoPlayer.tsx  # RTSP 视频播放器
│  │  ├── settings/
│  │  │  ├── SystemSettings.tsx   # 系统设置页面
│  │  │  └── LargeScreenSettings.tsx # 大屏设置页面
│  │  ├── large-screen/
│  │  │  └── LargeScreenView.tsx  # 大屏展示页面
│  │  ├── layout/
│  │  │  ├── Header.tsx           # 顶部导航栏
│  │  │  └── Sidebar.tsx          # 侧边栏菜单
│  │  └── ui/                      # shadcn/ui 基础组件
│  │      ├── button.tsx
│  │      ├── input.tsx
│  │      ├── dialog.tsx
│  │      ├── table.tsx
│  │      ├── tabs.tsx
│  │      ├── badge.tsx
│  │      ├── select.tsx
│  │      ├── toast.tsx / toaster.tsx
│  │      └── ...
│  │
│  ├── hooks/
│  │  ├── use-mobile.ts            # 移动端检测 Hook
│  │  └── use-toast.ts             # Toast 通知 Hook
│  │
│  └── lib/
│      └── utils.ts                 # 工具函数（cn 样式合并等）
│
├── tools/
│  └── generate_activation.py       # Ed25519 激活码生成工具（授权平台用）
│
├── data/                            # 运行时数据目录（自动创建）
│  └── private_key.hex              # Ed25519 私钥（仅授权平台使用）
│
├── public/                          # 静态资源
│  ├── logo.png                     # 门店 Logo
│  └── logo.svg                     # SVG 版 Logo
│
├── package.json                     # Node.js 依赖和脚本
├── next.config.ts                   # Next.js 配置（开发模式rewrites 代理 :8080）
├── tsconfig.json                    # TypeScript 配置
├── tailwind.config.ts               # Tailwind CSS 配置
├── postcss.config.mjs               # PostCSS 配置
├── eslint.config.mjs                # ESLint 配置
└── components.json                  # shadcn/ui 组件配置
```

---

## API 路由一览

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `/api/auth` | 登录密码验证 |
| GET | `/api/devices` | 获取所有设备列表（含采集状态） |
| POST | `/api/devices` | 创建设备（大华设备自动启动采集） |
| GET | `/api/devices/:id` | 获取单个设备详情 |
| PUT | `/api/devices/:id` | 更新设备（凭证变更自动重连） |
| DELETE | `/api/devices/:id` | 删除设备（自动停止采集） |
| PUT | `/api/devices/:id/status` | 设备状态（在线/离线/重连中） |
| POST | `/api/traffic` | 上报客流数据 |
| GET | `/api/traffic/history` | 历史客流查询（按日期/设备/范围）|
| GET | `/api/traffic/dashboard` | 仪表盘聚合数据|
| GET | `/api/traffic-collector/status` | 采集器状态详情|
| POST | `/api/traffic-collector/restart` | 重启采集器|
| GET | `/api/settings` | 获取系统设置 |
| PUT | `/api/settings` | 更新系统设置 |
| GET | `/api/license` | 获取 License 信息（含硬件指纹）|
| POST | `/api/license` | 激活 License（Ed25519 验证）|
| GET | `/api/license/parse` | 解析激活码（调试用）|
| POST | `/api/seed` | 生成测试数据 |
| GET | `/api/devices/:id/stream` | RTSP 视频流 (MJPEG) |
| GET | `/api/large-screen` | 获取大屏设置 |
| PUT | `/api/large-screen` | 更新大屏设置 |
| GET | `/api/large-screen/templates` | 大屏模板列表 |
| GET | `/api/health` | 健康检查|

---

## 环境要求

### 开发环境
- **Python** 3.8 ~ 3.12+（推荐 3.11）
- **Node.js** 18+
- **npm** 9+

### 打包环境（仅 Windows）
- Python 3.8 ~ 3.12+
- Node.js 18+
- **Inno Setup** 6.x（可选，用于生成安装程序）

---

## 快速开发

### 1. 克隆项目

```bash
git clone <repo-url>
cd FluxAvision
```

### 2. 安装 Python 依赖

```bash
cd backend
python -m venv venv

# Windows
venv\Scripts\activate
# Linux/macOS
source venv/bin/activate

pip install -r requirements.txt
```

### 3. 安装前端依赖

```bash
# 回到项目根目录
cd ..
npm install
```

### 4. 启动开发服务器

需要**同时启动后端和前端**（两个终端窗口）。

```bash
# 终端 1 —启动后端 (端口 8080)
cd backend
python main.py

# 终端 2 —启动前端 (端口 3000)
npm run dev
```

浏览器打开 `http://localhost:3000`，前端通过 rewrites 自动代理 `/api/*` 到后端 8080。

### 5. 大华 SDK（可选）

如果有大华 NetSDK wheel 包，放入 `backend/` 目录后安装：

```bash
pip install backend/NetSDK-2.0.0.1-py3-none-win_amd64.whl
```

> SDK 仅 Windows x64 可用，Linux/macOS 会自动跳过。

---

## 打包流程

### 方式一：一键构建（推荐）

```bash
cd backend
build.bat
```

`build.bat` 会自动执行以下 6 步：

| 步骤 | 说明 |
|------|------|
| 1/6 | 检查 Python + Node.js 环境 |
| 2/6 | 安装 Python 打包依赖（PyInstaller、pystray、Pillow）|
| 3/6 | 安装 Node.js 前端依赖 |
| 4/6 | 构建 Next.js 前端（临时切换为 export 模式，构建完恢复）|
| 5/6 | 生成应用图标 |
| 6/6 | PyInstaller 打包为 exe |

构建产物位置：`backend/dist/FluxAvision/FluxAvision.exe`。

### 方式二：手动分步构建

```bash
# 1. 安装打包依赖
cd backend
pip install pyinstaller pystray Pillow

# 2. 构建前端（需要临时修改 next.config.ts 的 output 为 "export"）
cd ..
npx next build

# 3. 复制前端构建产物
mkdir backend\frontend-build
xcopy out backend\frontend-build\ /E /I /Q

# 4. PyInstaller 打包
cd backend
python -m PyInstaller --clean --noconfirm FluxAvision.spec
```

### 生成安装程序（可选）

安装 [Inno Setup](https://jrsoftware.org/isinfo.php) 后：

```bash
cd backend
iscc installer.iss
```

安装程序输出：`installer_output/FluxAvision-Setup-v2.2.0.exe`。

---

## 打包后的运行方式

```bash
# 直接运行（后台静默模式，自动打开浏览器）
FluxAvision.exe

# 控制台模式（调试用，可以看到日志输出）
FluxAvision.exe --console

# 指定端口
FluxAvision.exe --port 9000

# 安装开机自启动
FluxAvision.exe --install

# 卸载开机自启动
FluxAvision.exe --uninstall
```

---

## 激活码生成

使用 `tools/generate_activation.py` 生成 Ed25519 签名激活码。

```bash
cd tools
python generate_activation.py \
  --fingerprint <32位硬件指纹> \
  --channels 4 \
  --days 365
```

输出格式：`FLUXA.{Base64URL(JSON载荷)}.{Base64URL(Ed25519签名)}`

载荷包含：硬件指纹前8位 + 最大路数 + 授权天数 + 签发时间戳。

---

## 数据目录说明

运行时自动在项目根目录（或 exe 同级目录）创建 `data/` 目录。

```
data/
├── FluxAvision.db          # SQLite3 数据库文件
├── FluxAvision.db-wal      # WAL 日志
├── FluxAvision.db-shm      # 共享内存
├── .key                    # AES 加密密钥文件（硬件指纹加密）
├── .salt                   # 随机盐值
└── FluxAvision.log         # 运行日志
```

> 数据库中敏感字段（设备密码、登录密码、激活码）存储为 `ENC:` 前缀的 AES-256 密文。

---

## 安全架构

```
┌──────────────────────────────────────────────────────────┐
│                    安全层级                              │
├──────────────────────────────────────────────────────────┤
│                                                         │
│ ● 硬件指纹绑定                                      │
│ └─ CPU序列号 + 主板序列号 + 磁盘序列号 + MAC → SHA-256  │
│                                                         │
│ ● 数据库密钥保护                                    │
│ └─ AES-256 密钥以硬件指纹派生密钥加密，存储于 .key 文件   │
│ └─ 硬件变更 → 密钥验证失败 → 自动重建（防拷贝）         │
│                                                         │
│ ● 敏感字段加密                                       │
│ └─ password / loginPassword / activationCode            │
│ └─ AES-256-CBC + PKCS7，每次加密使用随机 IV              │
│                                                         │
│ ● Ed25519 数字签名授权                               │
│ └─ 公钥内置客户端，私钥仅授权平台持有                     │
│ └─ 激活码包含指纹匹配 + 路数/天数限制                     │
│ └─ 无法伪造、无法破解、无法篡改                          │
│                                                         │
└──────────────────────────────────────────────────────────┘
```

---

## 故障排查

| 问题 | 解决方案 |
|------|----------|
| `pip install` 报错 | 确认 Python 版本 3.8+，尝试 `pip install --upgrade pip` |
| 端口 8080 被占用 | 修改 `backend/config.py` 的 `API_PORT` 或用 `--port` 参数 |
| 前端代理 502 | 确认后端已启动在 8080 端口 |
| 大华 SDK 不可用 | 仅支持 Windows x64，确认已安装 `.whl` |
| 数据库解密失败 | 删除 `data/.key` 和 `data/FluxAvision.db*` 重新初始化 |
| PyInstaller 打包失败 | 确认 `frontend-build/` 目录存在且有 `index.html` |
| 打包后前端空白 | 检查 `FluxAvision.spec` 的 `datas` 路径是否正确 |

