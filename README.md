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

