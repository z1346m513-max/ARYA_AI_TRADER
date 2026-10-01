# دستورالعمل استقرار حاکمیت ARYA AI Trader

این فایل برای همکاران پروژه تهیه شده تا تغییرات حاکمیتی PR #46 را دریافت، بررسی و در صورت تأیید مالک پروژه مستقر کنند.

مهم: ابتدا AGENTS.md و docs/governance/PLATFORM_CONSTITUTION.md را بخوانید. هیچ‌کس مجاز به Merge مستقیم یا تغییر main خارج از فرآیند PR نیست.

## 1. دریافت آخرین وضعیت

PowerShell:

    cd D:\AI\ARYA_AI_TRADER
    git fetch origin --prune
    git status
    git branch -a

## 2. دریافت branch حاکمیتی

    git fetch origin feat/platform-constitution-governance-2026-10-02
    git checkout feat/platform-constitution-governance-2026-10-02
    git pull --ff-only origin feat/platform-constitution-governance-2026-10-02

اگر branch وجود ندارد:

    git checkout -b feat/platform-constitution-governance-2026-10-02 --track origin/feat/platform-constitution-governance-2026-10-02

## 3. کنترل فایل‌های اجباری

    $required = @(
      "AGENTS.md",
      "docs/governance/PLATFORM_CONSTITUTION.md",
      "docs/governance/STARTUP_CHECKLIST.md",
      "docs/governance/CHANGE_LEDGER.md",
      "docs/governance/OWNER_AND_IP_POLICY.md",
      "docs/governance/IMPLEMENTATION_IMPROVEMENTS.md",
      "docs/sources/DRIVE_SOURCE_REGISTRY.md",
      "skills/arya-platform-governance/SKILL.md",
      ".github/CODEOWNERS",
      ".github/pull_request_template.md",
      ".github/workflows/governance.yml",
      "scripts/verify_governance.py"
    )
    $required | ForEach-Object {
      if (-not (Test-Path $_)) { throw "MISSING: $_" }
      Write-Host "OK: $_"
    }

## 4. کنترل Git

    git status --short
    git log --oneline -10
    git diff origin/main...HEAD --stat

هیچ secret، token، credential یا فایل موقت نباید بدون بررسی وارد commit شود.

## 5. کنترل Change Record

    Get-ChildItem docs/changes/CR-*.md | Select-Object Name
    Get-Content docs/governance/CHANGE_LEDGER.md

هر تغییر معنادار باید دارای CR-YYYYMMDD-NNN.md باشد و همان ID در Change Ledger ثبت شود.

## 6. بررسی Python و Governance

    python --version
    python scripts/verify_governance.py
    python -m compileall -q src tests scripts

## 7. نصب محیط توسعه

    .\.venv\Scripts\Activate.ps1
    python -m pip install --upgrade pip
    pip install -e ".[dev]"

## 8. اجرای تست‌ها

    pytest -q
    pytest tests/ -v

نتیجه واقعی تست باید در Change Record ثبت شود.

## 9. کنترل نهایی

    git diff --check
    git status
    git diff origin/main...HEAD

## 10. ایجاد تغییر جدید

    git checkout main
    git pull --ff-only origin main
    git checkout -b feat/<short-description>

قبل از کدنویسی باید AGENTS.md، Constitution، Startup Checklist، Change Ledger، ADRهای مرتبط و Source Registry خوانده شوند.

## 11. Evidence Gate

قبل از نوشتن کد باید منبع معتبر، URL/شناسه، تاریخ/نسخه، ادعای دقیق، روش اعتبارسنجی، اثر منبع بر طراحی و روش تست مشخص باشد.

اگر برای یک رفتار حیاتی evidence کافی وجود ندارد:

    STOP — UNVERIFIED

خروجی AI به‌تنهایی evidence محسوب نمی‌شود.

## 12. Commit و Push

    git add .
    git commit -m "feat: <short description>"
    git push -u origin feat/<short-description>

پیام commit جایگزین Change Record نیست.

## 13. Pull Request

PR باید دلیل، Change Record ID، منابع و evidence، تست‌ها، نتیجه تست، اثرات جانبی، migration در صورت وجود و وضعیت security را داشته باشد.

## 14. Merge

Merge فقط پس از عبور CI، بررسی Code Owner، بررسی Change Record، رفع review comments و تأیید مالک پروژه انجام شود.

## 15. Branch Protection برای main

این قسمت باید توسط مالک/Administrator انجام شود. در GitHub به Settings → Rules → Rulesets بروید.

Ruleset پیشنهادی: ARYA-main-governance-required

حداقل کنترل‌های پیشنهادی:
- Require a pull request before merging
- Require Code Owner review
- Require required status checks
- Require conversation resolution
- Dismiss stale approvals در صورت نیاز
- Require approval of the most recent reviewable push
- Block force pushes
- Block branch deletion

پس از فعال‌سازی، وضعیت واقعی آن باید در Change Record ثبت شود.

## 16. Google Drive

Drive-1: https://drive.google.com/drive/folders/1QS-0UJX2Hqwv_gEa0XTSuVJVu9pVouaW
Drive-2: https://drive.google.com/drive/folders/1p-mjgJI1IdPRf-j3olrvL8c--1-7XvlL

تا زمان فراهم‌شدن دسترسی واقعی، هیچ‌کس نباید ادعا کند فایل‌های این دو پوشه را خوانده یا در آن‌ها چیزی نوشته است.

پس از فعال‌شدن دسترسی: Inventory، File ID، Path/Name، MIME type، Modified time، SHA-256، Access date، Version، Evidence claims و Trust state ثبت شود.

Trust state مجاز: VERIFIED / PARTIAL / UNVERIFIED / REJECTED

## 17. شرایط توقف

در نبود منبع معتبر، تعارض منابع، API تأییدنشده، شکست تست حیاتی، ابهام license/IP، وجود secret در diff یا تعارض با Constitution، کار متوقف و موضوع با وضعیت BLOCKED ثبت شود.

## 18. پایان session

    git status
    git diff --check
    git log -1 --oneline

Change Record، Change Ledger، نتیجه تست و unresolvedها را به‌روزرسانی کنید.

## 19. سلسله‌مراتب مرجع

1. مالک پروژه
2. Platform Constitution
3. ADRهای مصوب
4. Source Registry و evidence
5. قراردادهای فنی
6. کد و تست‌های repository

خروجی AI، حدس شخصی یا اطلاعات بدون منبع در این سلسله‌مراتب مرجع محسوب نمی‌شود.