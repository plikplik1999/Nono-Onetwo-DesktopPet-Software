# Nono-Onetwo-DesktopPet-Software
一个运行在 Windows 桌面上的桌面宠物程序。布布和一二会在屏幕角落陪伴你，关心你的日常工作状态并贴心地提醒你起身活动、喝水、休息。

<p align="center">
  <img src="https://img.shields.io/badge/platform-Windows-blue" alt="platform">
  <img src="https://img.shields.io/badge/Python-3.11+-3776AB?logo=python&logoColor=white" alt="python">
  <img src="https://img.shields.io/badge/GUI-Tkinter-0078D4" alt="gui">
  <img src="https://img.shields.io/badge/打包-PyInstaller-important" alt="packaging">
  <img src="https://img.shields.io/badge/license-MIT-green" alt="license">
</p>

## 目录

- [项目介绍](#项目介绍)
- [功能特性](#功能特性)
- [角色系统](#角色系统)
- [安装与使用](#安装与使用)
- [配置说明](#配置说明)
- [项目结构](#项目结构)
- [技术文档](#技术文档)
- [从源码构建](#从源码构建)
- [常见问题](#常见问题)

---

## 项目介绍

DesktopPet 是一个纯本地运行的轻量桌面伴侣程序。它以一个透明、置顶的动图小窗口悬浮在桌面角落，可以随意拖动，并通过右键菜单与用户交互。

它会在后台默默关注你的工作状态，适时用气泡对话框弹出关怀提醒（久坐、喝水、长时间工作等），并带有 `谢谢 / 摸摸` 快捷按钮；点按 `摸摸` 会随机播放角色的音效，给你小小的陪伴感。

> 程序完全离线运行，不联网、不收集任何数据。所有动图与音频素材均内嵌在可执行文件中。

## 功能特性

- **透明置顶动图宠物**：无边框、透明背景、始终置顶，可拖动到屏幕任意位置。
- **多角色切换**：内置 `nono`、`onetwo` 两个角色，以及二者同框的 `both` 模式，右键菜单一键切换并记住选择。
- **随机动画**：每个角色拥有自己的动图库，按固定间隔随机循环播放。
- **摸摸互动**：`摸摸`（及各类提醒的「谢谢/摸摸」按钮）会随机播放当前角色的音效。
- **健康提醒**（气泡对话框 + 快捷按钮）：
  - 久坐提醒
  - 喝水提醒
  - 长时间工作提醒（随机回复池）
  - 离开问候（检测鼠标长时间无操作后回归）
  - 日常陪伴（每小时按概率随机问候）
  - 疲劳询问（频繁切换窗口后主动关心，可答「对 / 不对」）
- **气泡自动消失**：带按钮的气泡 10 秒未点击自动关闭。
- **设置面板**：右键菜单打开，可调整动画切换时长、各类提醒开关与间隔。
- **单实例运行**：重复启动会提示「已在运行」。
- **素材保护**：所有 gif / mp3 / wav 素材以 base64 内嵌进程序，不暴露任何素材文件。

## 角色系统

| 角色 | 说明 | 动图数 | 右键菜单切换选项 |
|------|------|--------|------------------|
| `onetwo` | 默认角色 | 58 | `布来！` → nono、`一起玩` → both |
| `nono` | 二号角色 | 83 | `宝来！` → onetwo、`一起玩` → both |
| `both` | 两个角色同框 | 44 | `布来！` → nono、`宝来！` → onetwo |

- 切换角色时播放对应「切换音效」（切 nono 播「换布布」、切 onetwo 播「换一二」、切 both 播「切换音效」）。
- 右键点击角色会播放当前角色的「点击音效」。
- 选中的角色会写入 `config.json`，下次启动沿用；首次启动默认 `onetwo`。

## 安装与使用

### 普通用户（推荐）

1. 下载 `dist/DesktopPet.exe`。
2. 双击运行，宠物即出现在屏幕左上角。
3. 右键点击宠物弹出菜单：
   - **切换角色**：`布来！` / `宝来！` / `一起玩`
   - **摸摸**：播放随机音效
   - **设置**：调整提醒与动画参数
   - **退出**：关闭程序

> `config.json` 会生成在 EXE 同目录下，可手动编辑（见[配置说明](#配置说明)）。

### 开发者（从源码运行）

```bash
# 1. 克隆 / 下载本项目
# 2. 安装依赖（Python 3.11+，Windows）
pip install pillow pyinstaller

# 3. 运行
python pet.py
```

## 配置说明

程序通过 `config.json`（EXE 同目录，或源码目录）配置。缺失的字段会自动使用默认值。

| 键 | 默认值 | 说明 |
|----|--------|------|
| `character` | `"onetwo"` | 当前角色：`nono` / `onetwo` / `both` |
| `switch_interval_seconds` | `4.0` | 动图切换间隔（秒） |
| `bubble_duration_seconds` | `6` | 普通气泡显示时长（秒） |
| `button_timeout_seconds` | `10` | 带按钮气泡未点击自动关闭时长（秒） |
| `sedentary_enabled` | `true` | 久坐提醒开关 |
| `sedentary_interval_minutes` | `45` | 久坐提醒间隔（分钟） |
| `water_enabled` | `true` | 喝水提醒开关 |
| `water_interval_minutes` | `30` | 喝水提醒间隔（分钟） |
| `idle_reset_minutes` | `10` | 闲置判定阈值（分钟） |
| `long_work_enabled` | `true` | 长时间工作提醒开关 |
| `long_work_minutes` | `120` | 长时间工作判定（分钟） |
| `away_enabled` | `true` | 离开问候开关 |
| `away_interval_minutes` | `15` | 鼠标静止判定时长（分钟） |
| `companion_enabled` | `true` | 日常陪伴开关 |
| `companion_interval_minutes` | `60` | 日常陪伴间隔（分钟） |
| `companion_probability` | `0.7` | 日常陪伴触发概率（0~1） |
| `window_switch_enabled` | `true` | 窗口切换疲劳询问开关 |
| `window_switch_threshold` | `8` | 触发询问的切换次数阈值 |
| `window_switch_window_minutes` | `5` | 切换计数窗口（分钟） |
| `window_switch_cooldown_minutes` | `30` | 询问冷却时间（分钟） |
| `switch_question_timeout_seconds` | `15` | 疲劳询问气泡时长（秒） |

可自定义的文案键（数组，随机取一条）：

- `messages_sedentary`：久坐提醒文案
- `messages_water`：喝水提醒文案
- `long_work_messages`：长时间工作文案
- `messages_away`：离开问候文案
- `companion_messages`：日常陪伴文案
- `switch_question` / `switch_answer_yes` / `switch_answer_no`：疲劳询问与回答

## 项目结构

```
Default Project/
├── pet.py                 # 主程序源码（全部逻辑）
├── assets_data.py         # 生成文件：内嵌素材（base64），勿手改
├── assets/                # 原始素材（开发用，不参与打包）
│   ├── audio/
│   │   ├── nono/          # nono 音效（含 换布布音效、点击音效）
│   │   ├── onetwo/        # onetwo 音效（含 换一二音效、点击音效）
│   │   └── both/          # both 音效（切换音效、点击音效）
│   └── skin/
│       ├── nono/          # nono 动图（*.gif）
│       ├── onetwo/        # onetwo 动图（*.gif）
│       └── both/          # both 动图（*.gif）
└── dist/
    ├── DesktopPet.exe     # 打包产物（用户直接使用）
    └── config.json        # 运行时配置
```

## 技术文档

### 技术栈

| 组件 | 用途 |
|------|------|
| Python 3.11+ | 开发语言 |
| Tkinter | GUI 窗口 / 气泡 / 菜单 / 设置面板 |
| Pillow (PIL) | GIF 解码、帧提取、等比缩放、RGBA 处理 |
| ctypes + Win32 | 系统级能力（详见下） |
| PyInstaller | 打包为单文件 EXE |

### 架构

核心逻辑集中在 `pet.py`，主要由以下类构成：

- **`DesktopPet`**：主控制器。负责窗口、动画循环、角色切换、提醒调度、菜单、设置与生命周期。
- **`ReminderBubble`**：气泡对话框（`Toplevel`）。支持文本、`谢谢/摸摸` 等按钮、点击空白关闭、自动超时消失，以及拖动时跟随宠物。
- **`AudioPlayer`**：音频播放器，基于 Windows MCI（`winmm.mciSendStringW`）。
- **`GifAnimation`**：单个动图（帧列表 + 每帧时长）。

### 关键实现

**1. 透明置顶窗口**

使用 `overrideredirect(True)` 去掉标题栏，`-topmost` 置顶，并通过 `-transparentcolor` 将背景色（`#010203`）设为透明，实现无边框透明宠物。

**2. GIF 动画与等比居中缩放**

原始动图分辨率不一（约 240~320px）且宽高比不同，程序统一在 100×100 窗口中显示：

```python
img.thumbnail(PET_SIZE, Image.Resampling.LANCZOS)   # 等比缩放适配
canvas = Image.new("RGBA", PET_SIZE, (0, 0, 0, 0))  # 透明画布
canvas.paste(img, (x, y), img)                       # 居中粘贴
```

动画通过 `root.after(delay, ...)` 逐帧播放，并按 `switch_interval_seconds` 随机切换下一个动图（用乱序播放列表避免与上一次重复）。

**3. 音频播放（wav / mp3）**

音频以字节形式内嵌，播放时先写入带随机前缀的临时文件，再调用 MCI：

```python
mtype = "waveaudio" if ext == ".wav" else "mpegvideo"
mciSendStringW(f'open "{path}" type {mtype} alias {alias}')
mciSendStringW(f"play {alias}")
```

播放结束（`stop`）后立即删除临时文件，避免素材残留。

**4. 提醒调度（1 秒心跳）**

`reminder_tick()` 通过 `root.after(1000, ...)` 每秒调度一次，集中处理所有定时/事件型提醒：

- **定时型**：久坐（`sedentary_start`）、喝水（`next_water_time`）、日常陪伴（`next_companion_time`，按概率触发）。
- **事件型**：
  - 长时间工作：活跃时长超过阈值。
  - 窗口切换疲劳：通过 `GetForegroundWindow` 统计前台窗口切换次数。
  - 离开问候：通过 `GetCursorPos` 轮询鼠标位置，静止超过阈值后在再次移动时触发。

**5. 气泡队列**

同时刻只显示一个气泡，新提醒进入队列，前一个关闭后依次弹出（`reminder_queue`）。

**6. 单实例**

使用命名互斥量 `Local\DesktopPetSingleton`（`CreateMutexW`）保证同一时间只运行一个实例。

**7. 素材内嵌与保护**

构建前由生成脚本把 `assets/` 下所有 gif/mp3/wav 转为 base64，写入 `assets_data.py`。运行时从内存（`BytesIO`）解码，成品中不存在任何素材文件，从源头避免素材被直接提取。

**8. 配置加载**

`load_config()` 将 `config.json` 与 `DEFAULT_CONFIG` 合并，缺失键自动补默认值；消息数组做空值校验回退。角色、参数改动通过 `save_config()` 持久化。

## 从源码构建

修改 `assets/` 素材或代码后，按以下步骤重新打包：

```bash
# 1. 重新生成内嵌素材（生成 assets_data.py）
python scripts/gen_assets_data.py

# 2. 打包为单文件 EXE
python -m PyInstaller --noconfirm --clean --onefile --noconsole \
  --name "DesktopPet" pet.py
```

产物输出到 `dist/DesktopPet.exe`。

> 若素材目录结构变化（新增角色 / 文件夹），需同步更新生成脚本中的角色列表。

## 常见问题

**Q：双击 EXE 提示「桌面宠物已在运行中」？**
程序单实例运行，请先右键宠物 → 退出，或到任务管理器结束 `DesktopPet` 进程。

**Q：宠物挡住了窗口怎么办？**
按住鼠标左键即可拖动到任意位置。

**Q：如何关闭某个提醒？**
右键宠物 → 设置，取消对应勾选后保存；或直接编辑 `config.json` 把对应 `*_enabled` 设为 `false`。

**Q：换了素材为什么不生效？**
素材是内嵌的，需重新生成 `assets_data.py` 并重新打包（见[从源码构建](#从源码构建)）。

**Q：支持哪些系统？**
仅支持 Windows（依赖 Win32 API 与 MCI）。

## 许可

MIT License
