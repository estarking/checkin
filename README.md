# 自用签到脚本

自用脚本，请勿传播。适用于多种 app 与论坛，解放双手自动化。适配青龙面板。适配青龙notify通知。已适配GitHub Actions。
selenium 自动化 python 脚本必须先安装 chromium 及 chromium-chromedriver。

## CloChat

适用于 CloChat 论坛，包含签到功能。

### 环境变量
- `CLOCHAT_USERNAME`: CloChat 的用户名（必需）
- `CLOCHAT_PASSWORD`: CloChat 的密码（必需）

## Nodeloc

适用于 Nodeloc 论坛，包含签到功能。
~~增加任务脚本，已实现自动点击话题及点赞功能。~~
为了论坛健康发展，已删除部分功能。

### 环境变量
- `NL_COOKIE`: NodeLoc 的 Cookie（必需）

## NodeSeek

适用于 NodeSeek 论坛，包含签到~~评论和加鸡腿~~功能。
~~强烈建议修改随机词，慎用ai评论功能。否则容易被举报被禁言~~。
为了论坛健康发展，已删除部分功能。

### 环境变量

- `NS_COOKIE`: NodeSeek 的 Cookie（必需）
- `NS_RANDOM`: 是否随机选择奖励，true/false（可选）
- `HEADLESS`: 是否使用无头模式，true/false（可选，默认 true）

## ArcticCloud

适用于 ArcticCloud，包含自动续期功能。

### 环境变量
- `ARCTIC_USERNAME`: ARCTIC 的用户名（必需）
- `ARCTIC_PASSWORD`: ARCTIC 的密码（必需）

## BinCloud

适用于 56IDC，包含登陆保号、检测vps状态、停机自动自动功能。

### 环境变量
- `BC_COOKIES`: 56IDC 的Cookie（必需）

## sfsy

适用于顺丰app，包含签到、抽奖、蜂蜜任务等功能。

### 环境变量
- `sfsyUrl`: 顺丰app捉包提取请求头中的url
