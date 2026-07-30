$mitmdump = "C:\Users\Administrator\AppData\Local\Programs\Python\Python313\Scripts\mitmdump.exe"

if (-not (Test-Path $mitmdump)) {
  Write-Error "mitmdump.exe not found at $mitmdump"
  exit 1
}

& $mitmdump `
  -s "scripts\wechat_stats_mitm_addon.py" `
  --set block_global=false `
  --set termlog_verbosity=info `
  --set flow_detail=1 `
  --listen-host 127.0.0.1 `
  --listen-port 8082
