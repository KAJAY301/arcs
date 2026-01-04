**Build .venv**
```
python -m venv .venv
```
**activate .venv**
```
Set-ExecutionPolicy RemoteSigned -Scope Process
.venv\Scripts\activate 
```
**dowwnload dependencies**
```
pip install -e .
```
**Download the right vervion of torch**
```
pip install torch torchvision --index-url https://download.pytorch.org/whl/cu118(depend on your GPU)
```

mock camera:
python test\mock_camera.py

model_result:
python test\model_result.py

.env的ip = PLC/parameter/ethernet port/IP address = ENET-L/Operational setting/IP address
test connection: CMD `ping "IP"`

PLC Y000 = X軸脈衝
    Y001 = Y軸脈衝
    Y002 = X軸方向
    Y003 = Y軸方向
"UP"  : Y001, Y003
"DOWN": Y001
"L"   : Y000, Y002
"R"   : Y000


# git 
**1. 將所有變更加入暫存區 (確認要存哪些檔案)**
git add .

**2. 建立存檔點 (寫下你這次改了什麼)**
git commit -m "修正關鍵點提取邏輯並優化繪圖顏色"

**3. 同步到 GitHub (推送到雲端)**
git push

**取得 GitHub 上最新的程式碼**
git pull

**回到上一次 commit 的狀態 注意：這會清除所有尚未 commit 的修改！**
git checkout .


如果你想嘗試一個很危險的功能（例如「自動裁切推論」），但不確定會不會改壞現有的穩定版本，可以開一個「分身」：
**1. 建立並切換到新分支**
git checkout -b feature-auto-crop

... 在這裡盡情改 Code ...

**2. 如果成功了，切換回 main 並合併**
git checkout main
git merge feature-auto-crop