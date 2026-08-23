@echo off
REM MasterNR1 Instagram ManyChat webhook — HTTPS tunnel (port 8055)
"C:\Program Files (x86)\cloudflared\cloudflared.exe" tunnel --url http://localhost:8055
