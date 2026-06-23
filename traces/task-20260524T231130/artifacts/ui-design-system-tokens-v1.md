# Cyberpunk Design System — 霓虹暗境

## Design Tokens

```css
:root {
  /* ── 背景层级 ── */
  --cyber-abyss:     #0a0a0f;    /* 最深黑 */
  --cyber-void:      #12121f;    /* 暗蓝紫底 */
  --cyber-surface:   #1a1a2e;    /* 面板底色 */
  --cyber-elevated:  #222240;    /* 悬浮面板 */
  
  /* ── 霓虹主色 ── */
  --neon-cyan:       #00f0ff;    /* 唐僧 · 系统架构师 */
  --neon-pink:       #ff00aa;    /* 八戒 · 产品黑客 */
  --neon-gold:       #ffd700;    /* 猴哥 · 全栈忍者 */
  --neon-green:      #00ff88;    /* 沙僧 · DevOps */
  --neon-purple:     #bf80ff;    /* 白龙马 · 布道师 */
  
  /* ── 功能色 ── */
  --neon-error:      #ff3333;    /* 错误/危险 */
  --neon-warn:       #ffaa00;    /* 警告 */
  --neon-success:    #00ff88;    /* 成功 = 沙僧绿 */
  
  /* ── 文字 ── */
  --text-primary:    #e0e0f0;    /* 冷白主文字 */
  --text-secondary:  #8888aa;    /* 灰紫辅助 */
  --text-muted:      #555577;    /* 暗灰 */
  
  /* ── 辉光 ── */
  --glow-cyan:       0 0 10px rgba(0,240,255,0.5), 0 0 40px rgba(0,240,255,0.15);
  --glow-pink:       0 0 10px rgba(255,0,170,0.5), 0 0 40px rgba(255,0,170,0.15);
  --glow-gold:       0 0 10px rgba(255,215,0,0.5), 0 0 40px rgba(255,215,0,0.15);
  --glow-green:      0 0 10px rgba(0,255,136,0.5), 0 0 40px rgba(0,255,136,0.15);
  
  /* ── 边框 ── */
  --border-subtle:   1px solid rgba(0,240,255,0.15);
  --border-active:   1px solid var(--neon-cyan);
  --border-glow:     1px solid rgba(0,240,255,0.4);
  
  /* ── 字体 ── */
  --font-mono:       "JetBrains Mono", "Fira Code", "SF Mono", monospace;
  --font-display:    "Orbitron", "Rajdhani", sans-serif;
  --font-body:       "Noto Sans SC", "PingFang SC", sans-serif;
  
  /* ── 动画时长 ── */
  --t-fast:          0.15s;
  --t-normal:        0.3s;
  --t-slow:          0.6s;
  --t-glitch:        0.1s;
  
  /* ── 间距 ── */
  --space-xs:        4px;
  --space-sm:        8px;
  --space-md:        16px;
  --space-lg:        24px;
  --space-xl:        32px;
}
```

## Agent Identity Colors

| Agent | Neon Color | Role | Icon |
|-------|-----------|------|------|
| 唐僧 | `--neon-cyan` `#00f0ff` | 系统架构师 | ⚡ |
| 八戒 | `--neon-pink` `#ff00aa` | 产品黑客 | 💾 |
| 猴哥 | `--neon-gold` `#ffd700` | 全栈忍者 | 🦾 |
| 沙僧 | `--neon-green` `#00ff88` | DevOps | 🔧 |
| 白龙马 | `--neon-purple` `#bf80ff` | 布道师 | 📡 |

## Card States

```css
.agent-card {
  background: var(--cyber-surface);
  border: var(--border-subtle);
  box-shadow: none;
  transition: all var(--t-normal);
}

.agent-card:hover {
  border-color: var(--neon-cyan);
  box-shadow: var(--glow-cyan);
}

.agent-card.active {
  border-color: var(--neon-cyan);
  box-shadow: var(--glow-cyan);
  animation: neon-pulse 2s infinite;
}

/* 状态变体 */
.agent-card[data-status="thinking"] { border-color: var(--neon-gold); box-shadow: var(--glow-gold); }
.agent-card[data-status="working"]  { border-color: var(--neon-green); box-shadow: var(--glow-green); }
.agent-card[data-status="error"]    { border-color: var(--neon-error); animation: glitch 0.3s; }
```

## Effects

```css
/* 扫描线 */
@keyframes scanline {
  0% { transform: translateY(-100%); }
  100% { transform: translateY(100vh); }
}

/* 霓虹脉冲 */
@keyframes neon-pulse {
  0%, 100% { box-shadow: var(--glow-cyan); }
  50% { box-shadow: 0 0 20px rgba(0,240,255,0.7), 0 0 60px rgba(0,240,255,0.25); }
}

/* 故障抖动 */
@keyframes glitch {
  0%, 100% { transform: translate(0); }
  20% { transform: translate(-2px, 1px); }
  40% { transform: translate(2px, -1px); }
  60% { transform: translate(-1px, -1px); }
  80% { transform: translate(1px, 1px); }
}

/* 数据粒子 */
@keyframes particle-float {
  0% { transform: translateY(0) translateX(0); opacity: 0; }
  50% { opacity: 0.8; }
  100% { transform: translateY(-100px) translateX(20px); opacity: 0; }
}

/* 打字机光标 */
@keyframes cursor-blink {
  0%, 100% { opacity: 1; }
  50% { opacity: 0; }
}

/* 全息旋转 */
@keyframes holo-spin {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}
```

## Component: Terminal Chat

```
┌─ TERMINAL // journey.log ─────────────────────────┐
│ >_ [14:23:11] 唐僧: 需求已接收，正在分析...        │
│ >_ [14:23:15] ⚡ 委派 → 八戒 (产品黑客)            │
│ >_ [14:23:42] 八戒 → 唐僧: PRD v1 已交付           │
│ >_ [14:23:45] 唐僧: 请确认需求方向是否正确          │
│                                                    │
│ ────────────────────────────────────────────────  │
│ $ _                                                 │
└────────────────────────────────────────────────────┘
```

## Component: File Vault

```
┌─ DATA_VAULT // outputs/ ──────────────────────────┐
│ 📦 PRD_v2.md                    12.4 KB  [DOWNLOAD]│
│ 📦 api_server.py                 8.2 KB  [DOWNLOAD]│
│ 📦 test_suite.py                 5.1 KB  [DOWNLOAD]│
└────────────────────────────────────────────────────┘
```
