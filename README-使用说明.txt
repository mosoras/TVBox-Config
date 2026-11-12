MOSORA 点播源在线检测网页（无需在自己的电脑安装 Python）

一、上传文件
1. 打开 https://github.com/mosoras/TVBox-Config
2. 点击 Add file -> Upload files
3. 解压本压缩包，把里面的 .github 文件夹、scripts 文件夹、site 文件夹，以及 README-使用说明.txt 上传到仓库根目录。
4. 不要删除或覆盖你原来的 tvbox.json、live.txt 等文件。
5. 点击 Commit changes。

二、启用网页
1. 打开仓库 Settings -> Pages
2. 在 Build and deployment 的 Source 中选择 GitHub Actions。
3. 保存（如果页面没有 Save 按钮则无需额外操作）。

三、运行检测
1. 打开仓库 Actions。
2. 选择 “MOSORA 点播源在线检测”。
3. 点击 Run workflow -> Run workflow。
4. 等待运行完成（绿色勾号）。
5. 网页地址为：https://mosoras.github.io/TVBox-Config/

之后每天会自动检测一次；修改 tvbox.json 后也会自动触发检测。

检测范围与限制
- type=1 且 api 是 HTTP/HTTPS 地址：由 GitHub 云端检查 HTTP 响应、状态码和常见 JSON/XML 格式。
- type=3 / csp_*：依赖 TVBox Spider/JAR，普通 HTTP 检查无法判断是否可用，会显示“需TVBox实测”，不把它误判为失效。
- “接口响应正常”不等于视频一定能播放；还需要在 TVBox 内抽样播放。
- 本工具只发起低并发、有限超时的基础请求，不会尝试绕过验证码、登录或付费限制。
