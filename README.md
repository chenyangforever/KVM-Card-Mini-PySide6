# forkKVM-Card-Mini

⌨️🖥️🖱️

Simple KVM Console to USB

一个简单的 KVM（Keyboard Video Mouse）设备控制卡，通过上位机程序控制被控设备的屏幕和键鼠。

---

## About

本项目修改自：

**https://github.com/Jackadminx/KVM-Card-Mini**

当前 PySide6 版本主要来源于：

**https://github.com/ElluIFX/KVM-Card-Mini-PySide6**

原 PySide6 项目增加了主题、音频路由、录制、截图、内置远程服务器（修改自 Open-IP-KVM）、屏蔽系统键、剪贴板、无需系统支持的文件传输、特殊按键键盘等功能，并迁移到 PySide6 以获得更好的 Nuitka 支持。

本 Fork 在此基础上主要补充 **Ubuntu/Linux 与 Intel macOS 的跨平台兼容性修复**。

> [!TIP]
> 如果需要寻找一个非自制获取硬件的方案，可参考：
>
> - [binnehot 的文章](https://github.com/binnehot/KVM_over_USB_Q05)
> - [do21 发现的问题](https://github.com/do21/KVM_over_USB_Q05)
>
> 上游项目曾在 [#4](https://github.com/ElluIFX/KVM-Card-Mini-PySide6/issues/4) 中记录 Linux/macOS 的跨平台兼容问题。
>
> 本 Fork 已针对 **Ubuntu 24.04** 和 **Intel macOS** 进行了真实硬件测试与适配。
>
> 基于 WebUSB 的纯浏览器客户端版本请参见上游 `web` 分支，感谢 @wang3076。

---

# 此 Fork 的状态

本 Fork 主要用于补充 `KVM-Card-Mini-PySide6` 在 Linux 和 macOS 上的跨平台兼容性。

当前实机测试硬件：

- KVM Card Mini HV2.6
- CH582F HID：`413d:2107`
- MacroSilicon MS2109 视频采集：`534d:2109`
- 视频设备名称：`YuzukiHCC V`

---

## Ubuntu 24.04

开发分支：

[`fix/ubuntu-linux-client`](https://github.com/chenyangforever/KVM-Card-Mini-PySide6/tree/fix/ubuntu-linux-client)

实机测试环境：

- Ubuntu 24.04.4 LTS
- x86_64
- Python 3.12
- PySide6
- KVM Card Mini HV2.6
- CH582F HID `413d:2107`
- MacroSilicon MS2109

### 已修复

- Linux 下 HID 设备初始化
- `hidapi` 在 Linux 下 `usage_page` 行为差异导致的设备识别问题
- Windows 专用 Qt 启动参数在 Linux 下的兼容问题
- PyQtDarkTheme 不同版本 API 的兼容问题
- Linux / Qt / XKB 原生扫描码转换
- Linux 键盘扫描码到 PC/AT Set-1 HID 扫描码的转换
- 实体键盘按键错位问题

### 已验证

- 视频采集正常
- HID 键盘控制正常
- HID 鼠标控制正常
- Ubuntu 实体键盘映射正常

例如修复前：

```text
Q W E R T
↓
O P [ ] Enter
```

修复后：

```text
Q W E R T
↓
Q W E R T
```

### 上游 PR

Ubuntu 修复已经提交给 ElluIFX 上游：

**https://github.com/ElluIFX/KVM-Card-Mini-PySide6/pull/12**

当前等待上游维护者处理。

---

## Intel macOS

开发分支：

[`fix/macos-camera-permission`](https://github.com/chenyangforever/KVM-Card-Mini-PySide6/tree/fix/macos-camera-permission)

详细安装、恢复、调试和 Nuitka 构建说明：

**[Docs/macOS-Intel.md](https://github.com/chenyangforever/KVM-Card-Mini-PySide6/blob/fix/macos-camera-permission/Docs/macOS-Intel.md)**

### 实机测试环境

- Intel MacBook Pro
- MacBookPro16,1
- Intel Core i9
- macOS 14.8.2
- x86_64
- Python.org CPython 3.11.9
- PySide6 6.11.x
- Nuitka 4.x
- KVM Card Mini HV2.6

### 已修复

#### macOS Camera Permission

增加 macOS 摄像头权限请求，并在 Nuitka App Bundle 中加入：

```text
NSCameraUsageDescription
```

解决 `.app` 无法正常取得视频采集设备权限的问题。

#### MacroSilicon MS2109 视频启动

调整 Qt Multimedia 摄像头初始化顺序：

```text
Camera
↓
QMediaCaptureSession
↓
VideoSink / Recorder / Audio
↓
camera.start()
```

避免摄像头启动过早导致 macOS 下视频无法正常工作的情况。

#### macOS 实体键盘

当前 Qt / macOS 环境下：

```text
nativeScanCode() == 0
```

因此改用：

```text
nativeVirtualKey()
```

建立：

```text
Apple Virtual Key Code
↓
PC/AT Set-1 Scan Code
↓
KVM HID
```

的转换关系。

Mac 修饰键对应：

```text
Control  → PC Ctrl
Option   → PC Alt
Command  → PC Windows / GUI
Shift    → PC Shift
```

#### HID QThread 正常退出

修复退出程序时：

```text
QThread: Destroyed while thread is still running
```

导致 `SIGABRT` 的问题。

退出时会正常停止：

```text
Camera
Server
HidThread
```

并等待 HID Thread 退出。

#### 启动时自动连接

原代码：

```python
QTimer().singleShot(...)
```

在 Nuitka + PySide6 环境中可能导致：

```text
TypeError:
QTimer.singleShot(...) is wrong (missing signature)
```

已修改为：

```python
QTimer.singleShot(...)
```

现在可以正常使用“启动时自动连接”。

#### macOS 高分辨率鼠标滚轮

Intel macOS 下，Qt 的 `QWheelEvent.angleDelta().y()` 并不总是传统鼠标常见的 `+120/-120`。

实机测试中可以出现：

```text
±24
±26
±70
±206
±410
±822
```

原程序仅在滚轮值严格等于 `+120/-120` 时发送 HID 滚轮事件，因此在 macOS 高分辨率鼠标环境下，轻微滚动或单格滚动可能没有反应。

当前版本已经修改为：

- 任意非零滚轮事件至少转换为 1 个 HID wheel step；
- 较大的 delta 按比例转换为多个 wheel step；
- 保留快速滚动时的速度差异。

已实机验证：

```text
单格滚动      OK
慢速连续滚动  OK
快速滚动      OK
向上/向下滚动 OK
```

### 已验证

Intel macOS 实机测试：

```text
CH582F HID 控制           OK
MacroSilicon MS2109 视频  OK
1920x1080 @ 30 fps        OK
Mac 实体键盘              OK
鼠标移动/点击             OK
高分辨率鼠标滚轮          OK
启动自动连接              OK
正常退出                  OK
Nuitka .app               OK
/Applications 安装        OK
```

> [!IMPORTANT]
> 当前 macOS 实机验证针对 **Intel Mac / x86_64**。
>
> Apple Silicon（arm64）尚未在本 Fork 中完成真实硬件验证。

---

## macOS 分支与 Ubuntu 分支的关系

目前：

```text
fix/macos-camera-permission
```

是在：

```text
fix/ubuntu-linux-client
```

基础上继续开发的。

当前提交关系大致为：

```text
upstream cross-platform
        │
        ├── Ubuntu compatibility fix
        ├── Ubuntu keyboard fix
        └── macOS compatibility fixes
```

因此暂时没有直接向上游提交 macOS Pull Request，以避免 macOS PR 重复包含 Ubuntu PR 的修改。

后续计划：

```text
Ubuntu PR #12 合并
        ↓
更新 cross-platform 基线
        ↓
整理独立 macOS 分支
        ↓
补齐 macOS Nuitka / GitHub Actions 构建配置
        ↓
提交独立 macOS PR
```

---

## 从 GitHub 恢复 Intel macOS 版本

如果以后重装系统或更换另一台 Intel Mac：

```bash
git clone https://github.com/chenyangforever/KVM-Card-Mini-PySide6.git

cd KVM-Card-Mini-PySide6

git switch fix/macos-camera-permission
```

然后参考：

**[Intel macOS 安装与构建说明](https://github.com/chenyangforever/KVM-Card-Mini-PySide6/blob/fix/macos-camera-permission/Docs/macOS-Intel.md)**

重新创建 Python 环境并构建 `.app`。

> [!NOTE]
> GitHub 当前保存的是：
>
> - 源代码
> - Git 修改历史
> - 构建说明
>
> `Client/build/`、Python 虚拟环境和本机生成的 `.app` 不会提交到 Git。
>
> 后续可以通过 GitHub Release 发布经过验证的 Intel macOS `.app`，实现直接下载使用。

---

## Screenshot

![Screenshot1](./Docs/Images/Screenshot1.png)

![Screenshot2](./Docs/Images/Screenshot2.png)

---

## Development

> [!IMPORTANT]
> 上游项目曾存在 Git 大小写问题：
>
> `Client/data` 可能没有自动从 `Data` 变更为 `data`。
>
> 如果遇到相关问题，请在编译前检查目录名称。
>
> 如果直接使用已经打包好的 Release 文件则通常不受影响。

上游跨平台开发版本位于：

```text
cross-platform
```

本 Fork 当前主要跨平台分支：

```text
fix/ubuntu-linux-client
fix/macos-camera-permission
```

---

## Upstream

本 Fork 基于：

**ElluIFX/KVM-Card-Mini-PySide6**

https://github.com/ElluIFX/KVM-Card-Mini-PySide6

其上游来源：

**Jackadminx/KVM-Card-Mini**

https://github.com/Jackadminx/KVM-Card-Mini

本 Fork 的主要目标不是替代原项目，而是记录、验证并贡献 Linux / Intel macOS 的跨平台兼容性修复。
