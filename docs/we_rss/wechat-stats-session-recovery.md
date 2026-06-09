# 微信文章统计 `no session` 排查与恢复

这份文档说明当 `we_rss` 的文章统计刷新接口返回
`WeChat stats refresh failed: no stats returned. Collector error: no session.`
时，你应该怎么处理。

这个错误不表示后端接口坏了，而是表示后端当前读取到的微信统计运行态已经失效，
或者根本没有抓到可用的微信会话数据。统计刷新依赖本机代理抓出来的
`session.json` 和 `proxy-live.log`，如果这两个文件是旧的，或者关键字段为空，
接口就拿不到阅读数、点赞数、分享数和评论数。

## 先看结论

当接口返回 `no session` 时，你要先刷新本机的微信统计运行态，再重新调用接口。

按最短路径操作：

1. 启动本地 `mitmproxy` 代理。
2. 打开 Windows 手动代理，指向 `127.0.0.1:8082`。
3. 安装并信任 `mitmproxy` 根证书。
4. 重启微信客户端。
5. 用微信内置浏览器打开一篇公众号文章。
6. 确认 `session.json` 和 `proxy-live.log` 刚刚更新。
7. 确认 `session.json` 里的 `appmsg_token`、`wap_sid2`、`wxuin`
   不是空值。
8. 再次调用文章统计刷新接口。

第 1 步可以直接执行下面两行命令：

```powershell
cd D:\GitHub\lipeaks_backend\scripts\lipeaks_viral_articles
powershell -ExecutionPolicy Bypass -File scripts\run-wechat-stats-proxy.ps1
```

## 为什么会报这个错

文章统计刷新接口不是直接用文章 HTML 就能拿到统计数据。当前实现会读取本机目录下
的微信运行态文件，然后回放微信统计接口。

后端固定读取下面这两个文件：

- `D:\GitHub\lipeaks_backend\scripts\lipeaks_viral_articles\output\wechat-stats\session.json`
- `D:\GitHub\lipeaks_backend\scripts\lipeaks_viral_articles\output\wechat-stats\proxy-live.log`

如果出现下面任一情况，接口就会失败：

- `session.json` 太旧，不是最近一次会话抓出来的。
- `proxy-live.log` 太旧，没有最近的文章访问记录。
- `session.json` 里关键字段为空。
- 微信流量根本没有经过本地代理。
- `mitmproxy` 证书没有正确安装到受信任根证书。

## 关键字段必须满足什么条件

`session.json` 至少要保证下面这些字段是有效的：

- `key`
- `uin`
- `pass_ticket`
- `appmsg_token`
- `wap_sid2`
- `wxuin`
- `wxtokenkey`

其中最容易出问题的是：

- `appmsg_token`
- `wap_sid2`
- `wxuin`

如果这三个字段是空值，统计接口大概率会返回 `no session`。

## 第一步：安装 mitmproxy

如果机器上还没有安装 `mitmproxy`，先执行：

```powershell
python -m pip install mitmproxy
```

安装完成后，验证命令是否可用：

```powershell
mitmdump --version
```

如果系统环境变量还没生效，也可以执行：

```powershell
python -m mitmproxy --version
```

## 第二步：启动本地代理

仓库里已经有代理启动脚本，路径是：

- `D:\GitHub\lipeaks_backend\scripts\lipeaks_viral_articles\scripts\run-wechat-stats-proxy.ps1`

启动命令：

```powershell
cd D:\GitHub\lipeaks_backend\scripts\lipeaks_viral_articles
powershell -ExecutionPolicy Bypass -File scripts\run-wechat-stats-proxy.ps1
```

如果你不想走脚本，也可以直接运行 `mitmdump`：

```powershell
cd D:\GitHub\lipeaks_backend\scripts\lipeaks_viral_articles
mitmdump -s "scripts\wechat_stats_mitm_addon.py" --set block_global=false --set termlog_verbosity=info --set flow_detail=1 --listen-host 127.0.0.1 --listen-port 8082
```

当前脚本默认监听：

- Host: `127.0.0.1`
- Port: `8082`

如果脚本启动成功，你可以另开一个 PowerShell 窗口确认进程存在：

```powershell
Get-Process mitmdump
```

## 第三步：打开 Windows 手动代理

代理进程启动后，还要把系统代理指向本机，否则微信流量不会经过 `mitmproxy`。

按下面步骤操作：

1. 打开 Windows **设置**。
2. 进入 **网络和 Internet**。
3. 打开 **代理**。
4. 在 **手动设置代理服务器** 中启用代理。
5. 地址填 `127.0.0.1`。
6. 端口填 `8082`。
7. 保存设置。

你也可以用 PowerShell 脚本直接设置当前用户代理：

启用代理到 `127.0.0.1:8082`：

```powershell
$reg = "HKCU:\Software\Microsoft\Windows\CurrentVersion\Internet Settings"
Set-ItemProperty -Path $reg -Name ProxyEnable -Type DWord -Value 1
Set-ItemProperty -Path $reg -Name ProxyServer -Type String -Value "127.0.0.1:8082"
Set-ItemProperty -Path $reg -Name ProxyOverride -Type String -Value "<local>"
```

关闭代理：

```powershell
$reg = "HKCU:\Software\Microsoft\Windows\CurrentVersion\Internet Settings"
Set-ItemProperty -Path $reg -Name ProxyEnable -Type DWord -Value 0
```

检查当前代理状态：

```powershell
Get-ItemProperty "HKCU:\Software\Microsoft\Windows\CurrentVersion\Internet Settings" |
  Select-Object ProxyEnable, ProxyServer, ProxyOverride
```

> **Warning:** 联调结束后记得关闭系统代理，避免影响其他应用联网。

## 第四步：安装并信任 mitmproxy 根证书

如果这台机器是第一次抓微信 HTTPS 流量，你必须安装证书，否则代理虽然跑着，
但微信请求通常无法被正确解密。

操作步骤如下：

1. 保持本地代理正在运行。
2. 在浏览器打开 `http://mitm.it`。
3. 下载当前系统对应的证书。
4. 双击证书文件开始安装。
5. 选择当前用户或本地计算机。
6. 选择“将所有的证书放入下列存储”。
7. 选择“受信任的根证书颁发机构”。
8. 完成导入。
9. 重启微信客户端。

> **Warning:** 证书必须导入到“受信任的根证书颁发机构”。如果导入错了证书库，
> 微信流量仍然抓不到。

## 第五步：重新抓取最新会话

代理、系统代理和证书都准备好之后，还要真的让微信流量跑一遍，才能生成新的
`session.json` 和 `proxy-live.log`。

按下面顺序操作：

1. 保持 `mitmdump` 正在运行。
2. 保持 Windows 手动代理开启。
3. 打开微信客户端。
4. 用微信内置浏览器打开一篇公众号文章。
5. 在文章页停留几秒。
6. 回到 PowerShell 检查运行态文件是否更新。

这里的重点是“微信内置浏览器打开文章”，不是普通 Chrome，也不是复制链接到别的
浏览器里打开。

## 第六步：检查文件是否已经更新

先检查 `proxy-live.log` 是否有新内容：

```powershell
Get-Content D:\GitHub\lipeaks_backend\scripts\lipeaks_viral_articles\output\wechat-stats\proxy-live.log -Tail 30
```

再检查 `session.json` 的修改时间：

```powershell
Get-Item D:\GitHub\lipeaks_backend\scripts\lipeaks_viral_articles\output\wechat-stats\session.json | Select-Object LastWriteTime
```

如果这两个文件的时间还是老的，说明这次微信流量没有真正经过代理。

## 第七步：检查关键字段是不是空值

运行下面这段命令，检查 `session.json` 的关键字段：

```powershell
@'
import json
from pathlib import Path

path = Path(r'D:\GitHub\lipeaks_backend\scripts\lipeaks_viral_articles\output\wechat-stats\session.json')
data = json.loads(path.read_text(encoding='utf-8'))

for key in [
    'appmsg_token',
    'wap_sid2',
    'wxuin',
    'wxtokenkey',
    'pass_ticket',
    'key',
    'uin',
]:
    print(key, bool(data.get(key)), data.get(key))
'@ | python -
```

你至少要看到下面这种结果：

- `appmsg_token True`
- `wap_sid2 True`
- `wxuin True`
- `pass_ticket True`
- `key True`
- `uin True`

如果 `appmsg_token`、`wap_sid2`、`wxuin` 还是 `False`，就不要继续调用刷新接口，
因为这次会话还是不可用。

## 第八步：如果日志更新了，但 session.json 还是不对

如果 `proxy-live.log` 已经有最新请求，但 `session.json` 还是不完整，你可以手动从
日志重新提取一次会话：

```powershell
python D:\GitHub\lipeaks_backend\scripts\lipeaks_viral_articles\scripts\wechat_session_from_log.py --log-file D:\GitHub\lipeaks_backend\scripts\lipeaks_viral_articles\output\wechat-stats\proxy-live.log
```

执行完后，再重复上一节的字段检查命令。

## 第九步：重新调用接口

确认 `session.json` 已经是最新的，且关键字段不为空之后，再重新调用：

```bash
curl 'http://localhost:8000/api/v1/we-rss/article-stats/refresh-by-url/' \
  -H 'Authorization: Bearer <token>' \
  -H 'Content-Type: application/json' \
  -H 'X-Tenant-ID: 3' \
  --data-raw '{"url":"https://mp.weixin.qq.com/s/RlBd6ySBEtGqt2I3-nNiTw"}'
```

如果运行态恢复成功，这次接口会返回文章对象，而不是：

```json
{
  "success": false,
  "code": 4000,
  "message": "WeChat stats refresh failed: no stats returned. Collector error: no session.",
  "data": null,
  "error_code": "VALIDATION_ERROR"
}
```

## 常见卡点

下面这些问题最常见。

### 代理已经启动，但文件时间没有更新

这通常表示微信流量没有走代理。优先检查：

1. Windows 手动代理是否真的指向 `127.0.0.1:8082`。
2. 微信是否在安装证书后重启过。
3. 打开的文章是否来自微信内置浏览器。

### proxy-live.log 有新内容，但 session.json 仍然为空字段

这通常表示抓到的请求不完整，或者证书没有真正生效。优先检查：

1. 证书是否导入到“受信任的根证书颁发机构”。
2. 微信客户端是否彻底退出后重开。
3. 当前文章页是否真的触发了微信统计请求。

### 接口返回 404

这不是代理问题，而是当前租户下没有这篇文章记录。
`refresh-by-url` 只刷新已存在文章的统计，不会按 URL 自动创建文章。

### 接口返回 400，但不是 no session

这时要直接看返回消息内容。当前后端已经改成显式报错，不会再把空统计伪装成成功。

## 你可以怎么判断这次恢复是否成功

如果同时满足下面三条，就可以认为恢复成功：

1. `session.json` 和 `proxy-live.log` 的修改时间都是刚刚更新的。
2. `session.json` 中 `appmsg_token`、`wap_sid2`、`wxuin` 都不是空值。
3. 重新调用 `refresh-by-url` 后，接口返回文章对象而不是 `VALIDATION_ERROR`。

## 下一步

如果你已经完成一次会话刷新，建议把下面两段输出保存下来，便于后续排查：

1. `session.json` 字段检查结果。
2. `proxy-live.log -Tail 30` 的输出。

这样下次再出现 `no session` 时，可以很快判断是代理没生效，还是会话过期。
