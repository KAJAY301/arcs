

```
Set-ExecutionPolicy RemoteSigned -Scope Process
.venv\Scripts\activate 
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