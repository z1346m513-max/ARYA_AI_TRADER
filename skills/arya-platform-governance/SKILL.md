# ARYA Platform Governance Skill

## Purpose
این Skill برای هر ایجنت یا دستیار هوش مصنوعی است که روی ARYA AI Trader کار می‌کند. هدف آن جلوگیری از تولید کد بر پایهٔ اطلاعات غیرمعتبر و ایجاد ردپای قابل ممیزی برای همهٔ تغییرات است.

## Mandatory startup
قبل از هر اقدام:
1. `AGENTS.md`
2. `docs/governance/PLATFORM_CONSTITUTION.md`
3. `docs/governance/STARTUP_CHECKLIST.md`
4. `docs/governance/CHANGE_LEDGER.md`
5. آخرین Change Recordها
6. ADRها و source registry مرتبط
را بخوان.

## Evidence Gate
برای هر تصمیم فنی:
- Primary source را پیدا کن.
- claim دقیق را ثبت کن.
- تاریخ/نسخه را ثبت کن.
- اگر امکان دارد با fixture، test یا نمونهٔ واقعی مستقل verify کن.
- اگر evidence کافی نیست: **STOP**.
- هرگز جای خالی evidence را با حدس پر نکن.
- خروجی LLM را evidence تلقی نکن.

## Coding Gate
قبل از نوشتن کد:
- scope و acceptance criteria روشن باشد.
- قرارداد داده/API مشخص باشد.
- منبع داده و freshness مشخص باشد.
- failure mode و fallback مشخص باشد.
- test strategy مشخص باشد.

## Change Gate
هر تغییر باید:
- یک `CR-YYYYMMDD-NNN.md` داشته باشد؛
- در `docs/governance/CHANGE_LEDGER.md` ثبت شود؛
- دلیل و evidence داشته باشد؛
- test output یا علت نبود test را ثبت کند؛
- در PR به Change Record ارجاع دهد.

## Multi-agent rule
ایجنت نباید فرض کند ایجنت دیگری اطلاعات معتبر دارد. هر session باید baseline را دوباره بررسی کند. تغییرات uncommitted یا تغییرات جدید branch باید قبل از کار بررسی شوند.

## Git rule
- مستقیم روی `main` کار نکن.
- branch مستقل بساز.
- PR باز کن.
- review و CI را منتظر بمان.
- merge فقط پس از پذیرش مالک پروژه.

## Drive rule
Drive-1 و Drive-2 مخازن مرجع هستند، اما تا زمانی که اتصال و manifest معتبر وجود نداشته باشد، اسناد آن‌ها UNVERIFIED هستند. دربارهٔ خواندن/نوشتن Drive ادعای ساختگی نکن.

## Output rule
در پاسخ/گزارش خود سه چیز را جدا نگه دار:
1. Fact / evidence
2. Assumption (اگر وجود دارد)
3. Decision / proposed implementation

## Stop conditions
اگر یکی از موارد زیر رخ داد، کار را متوقف کن:
- منبع متناقض یا نامعتبر؛
- API بدون مستندات کافی؛
- دادهٔ غیرقابل بازتولید؛
- نبود مجوز/مالکیت لازم؛
- شکست test حیاتی؛
- تعارض با Constitution.

## Owner authority
تصمیم نهایی پروژه با مالک `ziya1346` است. Skill مجاز نیست تصمیم مالک را جایگزین کند.
