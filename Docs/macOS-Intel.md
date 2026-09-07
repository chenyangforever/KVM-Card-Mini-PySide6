# KVM Card Mini PySide6 - Intel macOS 安装与构建说明

本文记录 `KVM-Card-Mini-PySide6` 在 Intel macOS 上的实机适配、构建和恢复方法。

主要目的：

- 记录已经验证可工作的 Intel macOS 环境；
- 方便以后重装系统或更换 Intel Mac 后重新构建；
- 记录本 Fork 针对 macOS 修复的问题和已知限制；
- 为后续整理上游 macOS Pull Request 提供测试依据。

---

## 1. 当前状态

代码分支：

```text
fix/macos-camera-permission
```

当前已在真实硬件环境下完成测试。

测试环境：

- MacBook Pro Intel（MacBookPro16,1）
- Intel Core i9
- macOS 14.8.2
- x86_64
- Python.org CPython 3.11.9
- PySide6 6.11.x
- Nuitka 4.x
- KVM Card Mini HV2.6

KVM Card Mini 主控端 USB 设备：

```text
413d:2107  Moyu at work Technology KVM Card Mini
534d:2109  MACROSILICON YuzukiHCC V
```

其中：

- `413d:2107`：CH582F HID / 键盘鼠标控制；
- `534d:2109`：MacroSilicon MS2109 UVC 视频采集。

---

## 2. 本 Fork 的 macOS 修复

本分支主要增加和修复以下内容。

### 2.1 macOS 摄像头权限

macOS 的摄像头访问受 TCC 权限管理。

直接运行：

```bash
python Mini-KVM.py
```

虽然 Qt 可以识别 `YuzukiHCC V`，但解释器本身没有 App Bundle 的
`Info.plist` 和 `NSCameraUsageDescription`，因此摄像头可能无法取得权限。

当前方案是使用 Nuitka 构建 `.app`，并在构建时加入：

```text
NSCameraUsageDescription
```

---

### 2.2 macOS 实体键盘

Qt 在当前 Intel macOS 环境中：

```text
event.nativeScanCode() == 0
```

因此不能直接沿用 Linux/Windows 的扫描码处理方法。

macOS 下改用：

```text
event.nativeVirtualKey()
```

并建立：

```text
Apple Virtual Key Code
        ↓
PC/AT Set-1 Scan Code
        ↓
KVM HID
```

的转换。

已验证普通字母、数字、方向键、修饰键和常用功能键。

Mac 修饰键对应关系：

```text
Control  → PC Ctrl
Option   → PC Alt
Command  → PC Windows / GUI
Shift    → PC Shift
```

---

### 2.3 Qt Multimedia 摄像头启动顺序

原程序在 Capture Session 尚未完全配置完成前就调用：

```python
camera.start()
```

并立即判断摄像头状态。

macOS 下可能因此导致视频无法正常启动。

当前版本改为：

```text
创建 Camera
    ↓
配置 QMediaCaptureSession
    ↓
配置 VideoSink / Recorder / Audio
    ↓
最后 camera.start()
```

已验证 MacroSilicon MS2109 可以稳定输出：

```text
1920 x 1080 @ 30 fps
```

---

### 2.4 HID QThread 正常退出

原程序退出时可能出现：

```text
QThread: Destroyed while thread is still running
```

并导致：

```text
SIGABRT
```

当前版本在退出时会依次清理摄像头、服务器和 HID Thread，并执行：

```text
HidThread.quit()
HidThread.wait()
```

已验证通过窗口关闭按钮正常退出后不会残留 `Mini-KVM` 进程。

---

### 2.5 启动时自动连接

原代码使用：

```python
QTimer().singleShot(...)
```

Nuitka + PySide6 环境下可能出现：

```text
TypeError:
QTimer.singleShot(...) is wrong (missing signature)
```

正确写法已经修改为：

```python
QTimer.singleShot(...)
```

因此现在可以正常启用：

```text
启动时自动连接
```

---

### 2.6 macOS 高分辨率鼠标滚轮

Intel macOS 实测中，Qt 的 `QWheelEvent.angleDelta().y()` 并不总是按照传统鼠标每格返回 `+120/-120`。

实际测试中可以出现：

```text
±24
±26
±70
±206
±410
±822
```

原程序仅判断：

```python
event.angleDelta().y() == 120
event.angleDelta().y() == -120
```

因此在 macOS 高分辨率鼠标环境下，大量较小的滚轮事件会被忽略，表现为轻微滚动或单格滚动没有反应。

当前版本已经修改为：

- 任意非零滚轮事件至少转换为 1 个 HID wheel step；
- 较大的 delta 按比例转换为多个 wheel step；
- 保留快速滚动时的速度差异。

已经实机验证：

```text
单格滚动      OK
慢速连续滚动  OK
快速滚动      OK
向上/向下滚动 OK
```

---

## 3. 从 GitHub 重新恢复源码

新机器或重装系统后：

```bash
git clone https://github.com/chenyangforever/KVM-Card-Mini-PySide6.git

cd KVM-Card-Mini-PySide6

git switch fix/macos-camera-permission
```

确认当前分支：

```bash
git branch --show-current
```

应该输出：

```text
fix/macos-camera-permission
```

可以查看当前版本：

```bash
git log -1 --oneline
```

注意：

默认 `git clone` 后通常位于 `main` 分支。

当前经过 Intel macOS 实机验证的修复代码位于：

```text
fix/macos-camera-permission
```

因此必须切换到该分支。

---

## 4. Python 环境

不建议使用 macOS 自带的 Apple Python。

本次验证使用 Python.org 官方 CPython 3.11。

当前机器上的解释器路径为：

```text
/Library/Frameworks/Python.framework/Versions/3.11/bin/python3.11
```

进入 Client：

```bash
cd ~/KVM-Card-Mini-PySide6/Client
```

创建独立虚拟环境：

```bash
/Library/Frameworks/Python.framework/Versions/3.11/bin/python3.11 \
  -m venv .venv311
```

激活：

```bash
source .venv311/bin/activate
```

升级基础工具：

```bash
python -m pip install --upgrade pip setuptools wheel
```

安装项目依赖：

```bash
pip install -r requirements.txt
```

安装 Nuitka：

```bash
pip install nuitka
```

检查依赖：

```bash
python -m pip check
```

确认 Python 架构：

```bash
python -c "import platform; print(platform.python_version(), platform.machine())"
```

Intel Mac 应看到：

```text
3.11.x x86_64
```

---

## 5. 构建 Intel macOS App

进入：

```bash
cd ~/KVM-Card-Mini-PySide6/Client
source .venv311/bin/activate
```

构建：

```bash
rm -rf build

python -m nuitka \
  --standalone \
  --static-libpython=no \
  --lto=no \
  --enable-plugin=pyside6 \
  --include-data-dir=./resources=resources \
  --include-qt-plugins=multimedia \
  --macos-create-app-bundle \
  --macos-target-arch=x86_64 \
  --macos-app-name="USB KVM Client" \
  --macos-app-icon=./resources/icons/icon.png \
  --macos-app-mode=gui \
  --macos-app-protected-resource="NSCameraUsageDescription:Access the HDMI capture device for KVM video" \
  --output-dir=build \
  Mini-KVM.py
```

成功后得到：

```text
Client/build/Mini-KVM.app
```

---

## 6. 首次运行

执行：

```bash
open "$HOME/KVM-Card-Mini-PySide6/Client/build/Mini-KVM.app"
```

macOS 首次运行时应申请摄像头权限。

允许 USB KVM Client 访问摄像头。

设备设置中选择：

```text
视频设备：YuzukiHCC V
分辨率：1920x1080
```

正常情况下窗口标题可以看到：

```text
USB KVM Client - 1920x1080 @ 30.0
```

---

## 7. 安装到 Applications

确认 build 版正常后：

```bash
pkill -x Mini-KVM 2>/dev/null || true

sudo rm -rf "/Applications/USB KVM Client.app"

sudo ditto \
  "$HOME/KVM-Card-Mini-PySide6/Client/build/Mini-KVM.app" \
  "/Applications/USB KVM Client.app"
```

启动：

```bash
open "/Applications/USB KVM Client.app"
```

之后可以像普通 macOS App 一样使用。

---

## 8. 建议验证项目

每次重新构建后建议确认：

```text
视频：1920x1080 @ 30 fps
实体键盘：正常
鼠标：正常
Control / Option / Command / Shift：正常
启动时自动连接：正常
关闭窗口：正常
退出后无 Mini-KVM 残留进程
```

检查残留进程：

```bash
ps -axo pid,command | grep '[M]ini-KVM'
```

正常退出后应无输出。

---

## 9. 常见问题

### 9.1 直接运行 Python 没有视频

如果：

```bash
python Mini-KVM.py
```

能够识别摄像头，但出现摄像头权限错误，这是当前 macOS TCC 行为导致的。

建议直接使用 Nuitka 构建后的 `.app`。

---

### 9.2 App 启动后立即崩溃

首先检查：

```bash
APP="$HOME/KVM-Card-Mini-PySide6/Client/build/Mini-KVM.app"

cat "$APP/Contents/MacOS/error.log"
```

如果存在真正的 Python Exception，应优先处理 `error.log` 中的第一条错误。

过去出现过：

```text
QThread: Destroyed while thread is still running
```

但它可能只是程序启动异常后产生的第二次错误，不一定是真正根因。

---

### 9.3 启动时自动连接导致崩溃

旧代码中的：

```python
QTimer().singleShot(...)
```

在 Nuitka/PySide6 环境中会出现错误。

当前分支已经修复为：

```python
QTimer.singleShot(...)
```

---

### 9.4 没有视频

可以先使用 macOS QuickTime Player 检查：

```text
YuzukiHCC V
```

是否能够正常显示 HDMI 输入。

如果 QuickTime 也没有画面，应先检查：

```text
HDMI 输入
USB 视频采集设备
USB 连接
```

而不是先修改程序。

---

## 10. 已知限制

当前版本主要针对：

```text
Intel Mac / x86_64
```

进行实机测试。

Apple Silicon：

```text
arm64
```

尚未在本 Fork 中完成实机验证。

当前：

```text
Client/.venv311/
Client/build/
```

均不会提交到 Git。

GitHub 保存的是：

```text
源码
构建说明
修改历史
```

而不是本机生成的 `.app`。

因此新机器恢复时需要重新创建 Python 环境并重新构建。

未来可以通过 GitHub Release 发布经过验证的 `.app`，从而实现直接下载使用。

另外，目前配置文件仍位于 App Bundle 附近。若未来进行正式代码签名和发行，
建议将用户配置迁移到：

```text
~/Library/Application Support/
```

等标准用户配置目录。

---

## 11. 与 Ubuntu 修复分支的关系

当前：

```text
fix/macos-camera-permission
```

是在：

```text
fix/ubuntu-linux-client
```

基础上继续开发的。

截至本文记录时，Ubuntu 修复已经提交上游：

```text
ElluIFX/KVM-Card-Mini-PySide6#12
```

macOS 分支暂未直接向上游创建 Pull Request，以避免重复包含 Ubuntu 修复。

后续计划：

```text
Ubuntu PR 合并
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

## 12. 当前已验证结论

KVM Card Mini HV2.6 在 Intel macOS 上已经验证：

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

这份文档用于保存当前已验证的恢复和构建流程，方便后续重新部署及继续开发。
