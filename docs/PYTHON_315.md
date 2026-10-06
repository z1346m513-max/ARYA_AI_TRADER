# سازگاری با Python 3.15

## نسخه پشتیبانی‌شده

```text
requires-python = ">=3.10,<3.16"
```

یعنی **3.10، 3.11، 3.12، 3.13، 3.14، 3.15**.

## نصب روی ویندوز با Python 3.15

```powershell
cd C:\Users\ziya\ARYA_AI_TRADER
git checkout feat/continue-tse-codal-2026-10-06

# venv را با همان 3.15 بسازید
py -3.15 -m venv .venv
# یا:
# C:\Users\ziya\AppData\Local\Programs\Python\Python315\python.exe -m venv .venv

.\.venv\Scripts\Activate.ps1
python -m pip install -U pip setuptools wheel
python -m pip install -e .
```

اگر `numpy` / `pandas` wheel برای 3.15 نداشتند:

```powershell
python -m pip install -U pip
python -m pip install numpy pandas --only-binary=:all:
```

در صورت شکست، یا صبر تا wheel رسمی، یا موقت از **Python 3.12** استفاده کنید (پایدارترین گزینه برای بورس):

```powershell
py -3.12 -m venv .venv312
.\.venv312\Scripts\Activate.ps1
python -m pip install -e .
```

## نکته launcher قدیمی

`arya.exe` که به Python313 حذف‌شده اشاره می‌کند را نادیده بگیرید:

```powershell
python -m arya.cli.main instrument --ticker FOOLAD
```

## تغییرات کد برای 3.15

- بدون وابستگی به API حذف‌شدهٔ stdlib
- type hints مدرن (`list[str]`, `|`)
- کف وابستگی‌ها بالا برده شد تا wheelهای جدیدتر انتخاب شوند
