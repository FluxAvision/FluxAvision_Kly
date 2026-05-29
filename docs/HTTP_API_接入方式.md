# 客流芸 HTTP API 接入方式

> 文档版本：v1.0  
> 适用范围：FluxAvision_Kly 客流统计系统  
> 服务端口：**15678**（默认），可通过环境变量 `API_PORT` 修改  
> 基础路径：所有 API 以 `/api/` 为前缀

---

## 目录

1. [通用说明](#1-通用说明)
2. [健康检查](#2-健康检查)
3. [设备管理 API](#3-设备管理-api)
4. [设备推送 API（双目客流相机）](#4-设备推送-api双目客流相机)
5. [客流数据 API](#5-客流数据-api)
6. [客流采集管理 API](#6-客流采集管理-api)
7. [仪表盘 API](#7-仪表盘-api)
8. [历史数据 API](#8-历史数据-api)
9. [认证 API](#9-认证-api)
10. [系统设置 API](#10-系统设置-api)
11. [大屏设置 API](#11-大屏设置-api)
12. [大屏模板 API](#12-大屏模板-api)
13. [License 管理 API](#13-license-管理-api)
14. [演示数据 API](#14-演示数据-api)
15. [视频流 API](#15-视频流-api)

---

## 1. 通用说明

### 1.1 统一响应格式

所有 API 返回 JSON 格式，外层统一结构：

```json
{
  "success": true,
  "data": { ... },
  "message": "操作成功"
}
```

**错误时：**

```json
{
  "success": false,
  "message": "错误描述"
}
```

HTTP 状态码：
| 状态码 | 含义 |
|--------|------|
| 200 | 成功 |
| 201 | 创建成功 |
| 400 | 请求参数错误 |
| 401 | 认证失败（密码错误） |
| 404 | 资源不存在 |
| 409 | 资源冲突（如设备序列号已存在） |
| 500 | 服务器内部错误 |

### 1.2 认证方式

- 系统不强制要求 Token / JWT 认证
- 仅 `/api/auth` 接口可用密码验证登录（本地校验）
- 外部设备推送（双目客流相机）无额外认证，直接通过 IP + 端口推送
- 建议在内网或 VPN 环境下部署；若需公网暴露，请在反向代理层添加认证

### 1.3 CORS

- 默认允许所有来源（`allow_origins: *`）
- 支持跨域请求，可通过环境变量 `CORS_ORIGINS` 配置

---

## 2. 健康检查

### `GET /api/health`

检查后端服务是否正常运行。

**请求示例：**

```http
GET /api/health
```

**响应示例：**

```json
{
  "success": true,
  "message": "FluxaVision 后端运行正常",
  "version": "2.0.0"
}
```

---

## 3. 设备管理 API

### 3.1 获取设备列表

#### `GET /api/devices`

获取所有摄像头设备列表，含采集器运行状态。

**请求示例：**

```http
GET /api/devices
```

**响应示例：**

```json
{
  "success": true,
  "data": [
    {
      "id": "a1b2c3d4e5f6g7h8i9j0k1l2m",
      "name": "正门入口",
      "ip": "192.168.1.101",
      "serialNumber": "DH-IPC-001",
      "location": "一楼正门",
      "model": "大华",
      "rtspPort": 554,
      "sdkPort": 37777,
      "channel": 0,
      "username": "admin",
      "password": "",
      "rtspUrl": "rtsp://admin:admin123@192.168.1.101:554/cam/realmonitor?channel=1&subtype=0",
      "maxChannels": 4,
      "status": "online",
      "collectorState": "connected",
      "createdAt": "2026-04-05T10:00:00",
      "updatedAt": "2026-04-05T10:00:00"
    }
  ]
}
```

**字段说明：**
| 字段 | 类型 | 说明 |
|------|------|------|
| id | string | 设备唯一 ID（25 位 hex） |
| name | string | 设备名称 |
| ip | string | IP 地址 |
| serialNumber | string | 设备序列号（唯一） |
| location | string | 安装位置 |
| model | string | 设备型号（大华/海康威视等） |
| rtspPort | int | RTSP 端口，默认 554 |
| sdkPort | int | SDK 端口，大华默认 37777 |
| channel | int | 客流统计通道号 |
| status | string | 在线状态：`online` / `offline` / `warning` |
| collectorState | string | 采集器状态：`connected` / `connecting` / `reconnecting` / `disconnected` / `stopped` / `not_started` |

---

### 3.2 获取单个设备

#### `GET /api/devices/{device_id}`

**请求示例：**

```http
GET /api/devices/a1b2c3d4e5f6g7h8i9j0k1l2m
```

**响应示例：** 同 3.1 的单个设备对象。

---

### 3.3 创建设备

#### `POST /api/devices`

创建新设备。若为"大华"设备，自动启动 SDK 客流采集。

**请求体：**

```json
{
  "name": "正门入口",
  "ip": "192.168.1.101",
  "serialNumber": "DH-IPC-001",
  "location": "一楼正门",
  "model": "大华",
  "rtspPort": 554,
  "sdkPort": 37777,
  "channel": 0,
  "username": "admin",
  "password": "admin123",
  "maxChannels": 4
}
```

**必填字段：** `name`、`ip`、`serialNumber`

**响应示例：**

```json
{
  "success": true,
  "data": {
    "id": "a1b2c3d4e5f6g7h8i9j0k1l2m",
    "name": "正门入口",
    "ip": "192.168.1.101",
    "serialNumber": "DH-IPC-001",
    ...
    "collectorStarted": true,
    "collectorMessage": "客流采集已自动启动"
  }
}
```

---

### 3.4 更新设备

#### `PUT /api/devices/{device_id}`

更新设备信息。如果大华设备的连接参数（IP/端口/用户名/密码/通道）发生变更，会自动重连 SDK。

**请求体：** （仅传需要更新的字段）

```json
{
  "name": "正门入口-更新",
  "password": "newpassword123"
}
```

---

### 3.5 删除设备

#### `DELETE /api/devices/{device_id}`

自动停止该设备的客流采集并清理 SDK 资源，同时删除关联的客流记录。

---

### 3.6 更新设备状态

#### `PUT /api/devices/{device_id}/status`

**请求体：**

```json
{
  "status": "online"
}
```

**支持状态值：** `online`、`offline`、`warning`

---

## 4. 设备推送 API（双目客流相机）

> 这是客流芸系统最重要的对外接口，用于双目客流相机（如 KLY 系列）通过 HTTP 协议推送客流数据。

**基础路径：** `/klyun/kl/equipapi/binocular`（固定前缀，兼容设备固件配置）

### 4.1 心跳上传

#### `POST /klyun/kl/equipapi/binocular/heartBeat`

设备上电后每分钟一次上传，用于监测设备在线状态。

**请求体：**

```json
{
  "version": 1,
  "macAddress": "4C:BC:98:60:10:8E",
  "ipAddress": "192.168.8.210",
  "connectionType": "Wired",
  "ipAddressMethod": "DHCP",
  "hostName": "Cam-13889",
  "timeZone": 8,
  "hwPlatform": "V3.0",
  "swRelease": "V6.3.6",
  "reportDate": "2023-04-17",
  "sn": "2010012104250097",
  "time": 1631947237
}
```

**请求体字段说明：**

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| sn | string | **是** | 设备序列号（用于匹配系统内的设备） |
| version | int | 否 | 接口版本 |
| macAddress | string | 否 | 设备 MAC 地址 |
| ipAddress | string | 否 | 设备 IP 地址 |
| connectionType | string | 否 | 连接方式：Wired / Wireless |
| hostName | string | 否 | 设备主机名 |
| timeZone | int | 否 | 时区偏移（如 8 表示 UTC+8） |
| hwPlatform | string | 否 | 硬件平台版本 |
| swRelease | string | 否 | 固件版本 |
| reportDate | string | 否 | 上报日期 |
| time | int | 否 | Unix 时间戳 |

**处理逻辑：**

1. 根据 `sn`（serialNumber）查找系统中已注册的设备
2. 如果找到，更新设备状态为 `online`，更新 IP 和名称
3. 如果未找到，返回 `code: 1`（设备未注册）

**成功响应：**

```json
{
  "code": 0,
  "msg": "success",
  "data": {
    "sn": "2010012104250097",
    "time": 1631947237
  }
}
```

**失败响应：**

```json
{
  "code": 1,
  "msg": "device not registered",
  "data": {}
}
```

---

### 4.2 数据上传

#### `POST /klyun/kl/equipapi/binocular/dataUpload`

有人进出时上传客流进出计数数据。支持实时上报（间隔=0）和间隔上报（间隔>0）两种模式。

**请求体：**

```json
{
  "version": 1,
  "macAddress": "4C:BC:98:60:10:8E",
  "ipAddress": "192.168.8.210",
  "connectionType": "Wired",
  "ipAddressMethod": "DHCP",
  "hostName": "Cam-13889",
  "timeZone": 8,
  "hwPlatform": "V3.0",
  "swRelease": "V6.3.6",
  "reportDate": "2023-04-17",
  "sn": "2010012104250097",
  "time": 1631947237,
  "startTime": 161231947237,
  "endTime": 1631947237,
  "in": 1,
  "out": 2,
  "passby": 2,
  "turnback": 3,
  "avgStayTime": 2000
}
```

**请求体字段说明：**

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| sn | string | **是** | 设备序列号 |
| endTime | int | **是** | 数据结束时间（Unix 毫秒时间戳），用于确定数据归属日期和小时 |
| startTime | int | 否 | 数据起始时间（Unix 毫秒时间戳） |
| in | int | 否 | 该时段内进入人数 |
| out | int | 否 | 该时段内离开人数 |
| passby | int | 否 | 经过人数 |
| turnback | int | 否 | 折返人数 |
| avgStayTime | int | 否 | 平均逗留时间（毫秒） |
| time | int | 否 | 当前上传数据的最新时间 |
| reportDate | string | 否 | 上报日期 |

**处理逻辑：**

1. 根据 `sn` 查找设备
2. 如果未找到，返回 `code: 1`（设备未注册）
3. 根据 `endTime` 计算出日期（`YYYY-MM-DD`）和小时（`0-23`）
4. 在该设备的 `deviceId + 日期 + 小时` 的 TrafficRecord 上进行**累加**：
   - `countIn += in`
   - `countOut += out`
   - `passby += passby`
   - `turnback += turnback`
   - `avgStayTime` 取最新值（覆盖）
5. 同时更新设备状态为 `online`

**成功响应：**

```json
{
  "code": 0,
  "msg": "success",
  "data": {
    "sn": "2010012104250097",
    "time": 1631947237
  }
}
```

**响应字段说明：**

| 字段 | 类型 | 说明 |
|------|------|------|
| code | int | 返回状态码：`0`=成功，`1`=失败 |
| msg | string | 返回信息 |
| data.sn | string | 设备 SN |
| data.time | int | 服务器 Unix 时间戳（设备用此字段同步时间） |

### 4.3 设备配置说明

外部双目客流相机在设备端设置推送地址时：

- **推送地址：** `http://<服务器IP>:15680/klyun/kl/equipapi/binocular/dataUpload`
- **心跳地址：** `http://<服务器IP>:15680/klyun/kl/equipapi/binocular/heartBeat`
- **上传间隔：** 可设置为 `0`（实时上报）或大于 0 的整数（固定间隔上报）
- 设备 SN 必须提前在客流芸系统中创建设备时录入（`serialNumber` 字段）

---

## 5. 客流数据 API

### 5.1 写入客流记录

#### `POST /api/traffic`

创建或更新客流记录。用于外部系统自行推客流数据（非相机推送场景）。

**请求体：**

```json
{
  "date": "2026-04-05",
  "hour": 14,
  "deviceId": "a1b2c3d4e5f6g7h8i9j0k1l2m",
  "countIn": 15,
  "countOut": 10
}
```

**字段说明：**

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| date | string | **是** | 日期 `YYYY-MM-DD` |
| hour | int | **是** | 小时 `0-23` |
| deviceId | string | 否 | 设备 ID（不传则默认为汇总记录） |
| countIn | int | 否 | 进入人数，默认 0 |
| countOut | int | 否 | 出去人数，默认 0 |

**处理逻辑：**

- 如果 `deviceId + date + hour` 的记录已存在，则 `countIn` 和 `countOut` **累加**到已有记录
- 如果不存在，则创建新记录

**响应示例：**

```json
{
  "success": true,
  "data": {
    "id": "x1y2z3...",
    "deviceId": "a1b2c3...",
    "date": "2026-04-05",
    "hour": 14,
    "countIn": 15,
    "countOut": 10
  }
}
```

---

### 5.2 累计客流统计

#### `GET /api/traffic/stats/cumulative`

获取所有设备（或指定设备）的累计客流统计。

**查询参数：**

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| deviceId | string | 否 | 设备 ID，不传则返回所有设备 |

**响应示例：**

```json
{
  "success": true,
  "data": [
    {
      "deviceId": "a1b2c3...",
      "deviceName": "正门入口",
      "totalIn": 10000,
      "totalOut": 9500,
      "currentInside": 500,
      "lastResetAt": null,
      "updatedAt": "2026-05-29T10:00:00"
    }
  ]
}
```

---

### 5.3 小时客流统计

#### `GET /api/traffic/stats/hourly`

查询指定日期内的小时级客流统计（含去重）。

**查询参数：**

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| date | string | 否 | 日期 `YYYY-MM-DD`，默认今日 |
| deviceId | string | 否 | 设备 ID，不传则门店级汇总 |
| startHour | int | 否 | 开始小时 0-23 |
| endHour | int | 否 | 结束小时 0-23 |

**响应示例：**

```json
{
  "success": true,
  "data": {
    "date": "2026-05-29",
    "hourly": [
      {
        "hour": 10,
        "countIn": 50,
        "countOut": 45,
        "countInUnique": 42,
        "countOutUnique": 38,
        "insideCount": 5
      }
    ]
  }
}
```

---

### 5.4 每日客流统计

#### `GET /api/traffic/stats/daily`

查询指定日期范围内的每日客流统计（含去重）。

**查询参数：**

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| startDate | string | **是** | 起始日期 `YYYY-MM-DD` |
| endDate | string | **是** | 结束日期 `YYYY-MM-DD` |
| deviceId | string | 否 | 设备 ID，不传则门店级汇总 |

**响应示例：**

```json
{
  "success": true,
  "data": {
    "startDate": "2026-05-01",
    "endDate": "2026-05-29",
    "daily": [
      {
        "date": "2026-05-01",
        "countIn": 500,
        "countOut": 480,
        "countInUnique": 420,
        "countOutUnique": 400,
        "insideMax": 50,
        "insideMin": 5
      }
    ]
  }
}
```

---

### 5.5 实时客流数据

#### `GET /api/traffic/stats/realtime`

获取采集器实时客流数据（需大华 SDK 运行中）。

**查询参数：**

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| deviceId | string | 否 | 设备 ID，不传则返回所有设备 |

**响应示例：**

```json
{
  "success": true,
  "data": [
    {
      "deviceId": "a1b2c3...",
      "deviceName": "正门入口",
      "enteredToday": 100,
      "exitedToday": 90,
      "insideNow": 10,
      "lastUpdate": "...",
      "collecting": true,
      "state": "connected"
    }
  ]
}
```

---

### 5.6 重置累计客流

#### `POST /api/traffic/stats/reset-cumulative`

重置指定设备的累计客流统计数据，常用于门店重开业或统计周期重置。

**请求体：**

```json
{
  "deviceId": "a1b2c3..."
}
```

**响应示例：**

```json
{
  "success": true,
  "data": {
    "deviceId": "a1b2c3...",
    "message": "累计客流统计已重置",
    "resetAt": "2026-05-29T10:00:00"
  }
}
```

---

## 6. 客流采集管理 API

> 用于管理大华 SDK 客流采集器的运行状态。通常不需要手动调用——设备添加后会自动启动。

### 6.1 获取采集器状态

#### `GET /api/traffic-collector/status`

**响应示例：**

```json
{
  "success": true,
  "data": {
    "sdkAvailable": true,
    "deviceCount": 2,
    "devices": [
      {
        "deviceId": "a1b2c3...",
        "enteredToday": 120,
        "exitedToday": 95,
        "insideNow": 25,
        "state": "connected",
        "reconnectAttempts": 0,
        "lastError": "",
        "lastConnectedAt": "2026-04-05T10:00:00",
        "lastStatTime": "2026-04-05T10:05:00"
      }
    ]
  }
}
```

### 6.2 获取实时客流

#### `GET /api/traffic-collector/realtime?deviceId={device_id}`

`deviceId` 可选，不传返回所有设备。

### 6.3 手动控制采集

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `/api/traffic-collector/start` | 手动启动指定设备采集 |
| POST | `/api/traffic-collector/stop` | 手动停止指定设备采集 |
| POST | `/api/traffic-collector/restart` | 重启指定设备采集（连接参数变更后） |

**请求体示例（start/stop/restart）：**

```json
{
  "deviceId": "a1b2c3...",
  "ip": "192.168.1.101",
  "port": 37777,
  "username": "admin",
  "password": "admin123",
  "channel": 0
}
```

---

## 7. 仪表盘 API

### `GET /api/traffic/dashboard`

获取仪表盘聚合数据，包括门店级汇总、各设备今日明细、逐时趋势。

**响应示例：**

```json
{
  "success": true,
  "data": {
    "storeName": "我的门店",
    "storeTotal": {
      "todayIn": 150,
      "todayOut": 120,
      "currentIn": 30,
      "weekIn": 850,
      "weekOut": 720,
      "monthIn": 3500,
      "monthOut": 3100,
      "yearIn": 15000,
      "yearOut": 13800,
      "totalIn": 50000,
      "totalOut": 45000,
      "instantaneousMaxCapacity": 200,
      "storeMaxCapacity": 500,
      "availableCapacity": 470
    },
    "devicesToday": [
      {
        "deviceId": "a1b2c3...",
        "deviceName": "正门入口",
        "deviceIp": "192.168.1.101",
        "deviceLocation": "一楼正门",
        "deviceStatus": "online",
        "todayIn": 80,
        "todayOut": 60,
        "currentInside": 20,
        "percentage": 53.3
      }
    ],
    "hourlyToday": [
      { "hour": 0, "countIn": 0, "countOut": 0 },
      { "hour": 1, "countIn": 0, "countOut": 0 }
    ],
    "peakHour": 12,
    "devices": [ "...设备列表..." ]
  }
}
```

---

## 8. 历史数据 API

### `GET /api/traffic/history`

查询历史客流数据，支持按时间范围和维度筛选。

**查询参数：**

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| startDate | string | 否 | 起始日期 `YYYY-MM-DD` |
| endDate | string | 否 | 结束日期 `YYYY-MM-DD` |
| deviceId | string | 否 | 设备 ID |
| dimension | string | 否 | 时间维度：`hourly`（小时） / `daily`（天） ，默认 `daily` |

### `PUT /api/traffic/history/correct`

修正指定时段客流记录。如果记录已存在则覆盖更新，不存在则创建。

**请求体：**

```json
{
  "date": "2026-04-05",
  "hour": 14,
  "countIn": 20,
  "countOut": 15,
  "deviceId": "a1b2c3..."
}
```

**请求体字段说明：**

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| date | string | **是** | 日期 `YYYY-MM-DD` |
| hour | int | **是** | 小时 `0-23` |
| countIn | int | 否 | 进入人数（修正值），默认 0 |
| countOut | int | 否 | 离开人数（修正值），默认 0 |
| deviceId | string | 否 | 设备 ID，不传则修正门店汇总记录 |

---

## 9. 认证 API

### `POST /api/auth`

验证登录密码。

**请求体：**

```json
{
  "password": "mypassword"
}
```

**响应示例（成功）：**

```json
{
  "success": true,
  "data": {
    "authenticated": true,
    "storeName": "我的门店",
    "isFirstLogin": false
  }
}
```

> **注意：**
> - 未设置密码时（首次使用），`authenticated: true` + `isFirstLogin: true`
> - 密码存储在 `SystemSettings.loginPassword` 中，使用 AES-256 字段加密

---

## 10. 系统设置 API

### 10.1 获取系统设置

#### `GET /api/settings`

### 10.2 更新系统设置

#### `PUT /api/settings`

**请求体：**

```json
{
  "storeName": "我的门店",
  "storeLogo": "",
  "loginPassword": "newpassword",
  "storeMaxCapacity": 500,
  "instantaneousMaxCapacity": 200,
  "dashboardMetrics": "todayIn,todayOut,currentIn,weekIn",
  "dashboardMetricsLabels": "{\"todayIn\": \"今日进店\"}"
}
```

---

## 11. 大屏设置 API

### 11.1 获取大屏设置

#### `GET /api/large-screen`

### 11.2 更新大屏设置

#### `PUT /api/large-screen`

**请求体：**

```json
{
  "title": "客流统计大屏",
  "subtitle": "实时客流数据展示",
  "logo": "",
  "backgroundImage": "",
  "backgroundColor": "#0a192f",
  "metrics": "todayIn,todayOut,currentIn",
  "deviceIds": "device_id_1,device_id_2",
  "templateId": "template_id_xxx"
}
```

> 指标最多可选 4 个。

---

## 12. 大屏模板 API

### 12.1 获取模板列表

#### `GET /api/large-screen/templates`

### 12.2 获取单个模板

#### `GET /api/large-screen/templates/{template_id}`

### 12.3 创建模板

#### `POST /api/large-screen/templates`

**请求体：**

```json
{
  "name": "我的模板",
  "description": "自定义模板",
  "templateConfig": {"widgets": []},
  "canvasWidth": 1920,
  "canvasHeight": 1080,
  "backgroundColor": "#0a192f",
  "backgroundImage": ""
}
```

### 12.4 更新模板

#### `PUT /api/large-screen/templates/{template_id}`

### 12.5 删除模板

#### `DELETE /api/large-screen/templates/{template_id}`

### 12.6 复制模板

#### `POST /api/large-screen/templates/{template_id}/duplicate`

**请求体：**

```json
{
  "name": "模板副本"
}
```

---

## 13. License 管理 API

### 13.1 获取 License 信息

#### `GET /api/license`

返回当前激活状态、硬件指纹、到期日期等。

### 13.2 激活 License

#### `POST /api/license`

**请求体：**

```json
{
  "activationCode": "FLUXA.{payload}.{signature}"
}
```

**验证流程：**

1. Ed25519 签名验证（防伪造）
2. 硬件指纹匹配（防跨机器使用）
3. 解析路数、天数等参数

### 13.3 解析激活码（调试用）

#### `GET /api/license/parse?code=FLUXA.xxx.yyy`

不验证签名，仅查看明文载荷内容。

---

## 14. 演示数据 API

### `POST /api/seed`

生成演示客流数据。

**请求体：**

```json
{
  "days": 30
}
```

> 默认生成 30 天、3 个设备的演示数据。（仅当数据库为空时可用）

---

## 15. 视频流 API

### 15.1 WebSocket 实时视频流

#### `WS /api/devices/{device_id}/stream/ws`

WebSocket 协议，每秒约 15 帧推送二进制 JPEG 帧。

**使用方式：**

```javascript
// 前端示例
const ws = new WebSocket(`ws://${host}/api/devices/${deviceId}/stream/ws`);
ws.binaryType = "arraybuffer";
ws.onmessage = (event) => {
  const blob = new Blob([event.data], { type: "image/jpeg" });
  const url = URL.createObjectURL(blob);
  imgElement.src = url;
};
```

### 15.2 MJPEG HTTP 流（兼容旧版）

#### `GET /api/devices/{device_id}/stream`

返回 `multipart/x-mixed-replace` 格式的 MJPEG 流，可直接赋值给 `<img>` 标签的 `src` 属性。

```html
<img src="http://server:15678/api/devices/{device_id}/stream" />
```

### 15.3 单帧快照

#### `GET /api/devices/{device_id}/snapshot`

返回单个 JPEG 帧。

### 15.4 视频流状态

#### `GET /api/devices/{device_id}/stream/status`

返回设备流状态信息。

---

## 附录

### A. 数据模型关系

```
Device                          TrafficRecord
┌──────────────────────┐        ┌──────────────────────────┐
│ id (PK)              │◄──┐    │ id (PK)                  │
│ serialNumber (唯一)   │   └────│ deviceId (FK → Device.id)│
│ name / ip / status   │        │ date (YYYY-MM-DD)        │
│ password (AES加密)    │        │ hour (0-23)              │
│ rtspUrl / channel    │        │ countIn / countOut       │
│ ...                  │        │ passby / turnback        │
└──────────────────────┘        │ avgStayTime              │
                                └──────────────────────────┘
```

### B. 外部设备推送流程

```
双目客流相机                         客流芸系统 (服务器)
     │                                      │
     │  ── POST /heartBeat (每分钟) ──────→  │
     │                                      │── 根据 sn 匹配设备
     │  ←── { code:0, sn:xxx, time:xxx } ──│── 更新设备 online 状态
     │                                      │
     │  ── POST /dataUpload (有人经过时) ──→  │
     │                                      │── 根据 sn 匹配设备
     │  ←── { code:0, sn:xxx, time:xxx } ──│── 按 date+hour 累加客流
     │                                      │── 更新设备 online 状态
```

### C. 设备配置说明（相机端）

在双目客流相机的配置界面中：

- **服务器地址：** 客流芸系统部署机器的 IP 或域名
- **端口：** 15678（默认 API 端口）
- **推送路径：** `/klyun/kl/equipapi/binocular/dataUpload`
- **心跳路径：** `/klyun/kl/equipapi/binocular/heartBeat`
- **上传间隔：** `0` 为实时上报，大于 0 为固定间隔（秒）
- **设备 SN：** 需提前在客流芸系统中添加设备时录入相同 SN

### D. 常见问题

**Q: 设备推送数据后一直返回 `code: 1, msg: "device not registered"`？**

A: 说明设备 SN 未在系统中注册。请先在客流芸的「设备管理」中添加设备，确保 `serialNumber` 与相机推送的 `sn` 一致。

**Q: 系统支持多少台设备同时推送？**

A: 无软件限制，取决于 License 授权路数和服务器的处理能力。

**Q: 推送数据是否会覆盖历史记录？**

A: 不会。同 `deviceId + date + hour` 的客流数据是**累加**的，即同小时内多次推送的 `in` 和 `out` 会累加。

**Q: 数据上传的时间戳格式是毫秒还是秒？**

A: 支持两种格式自动兼容。13 位数字按毫秒处理（除以 1000），10 位数字按秒处理。
