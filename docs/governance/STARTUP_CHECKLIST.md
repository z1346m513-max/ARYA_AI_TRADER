# چک‌لیست اجباری شروع کار

این چک‌لیست برای هر session انسانی یا AI است.

## A. خواندن baseline
- [ ] `AGENTS.md`
- [ ] `docs/governance/PLATFORM_CONSTITUTION.md`
- [ ] `docs/governance/CHANGE_LEDGER.md`
- [ ] آخرین فایل‌های `docs/changes/`
- [ ] ADR مرتبط در `docs/decisions/`
- [ ] `docs/sources/`
- [ ] README و معماری مرتبط

## B. بررسی وضعیت
- [ ] branch جاری مشخص است.
- [ ] base branch مشخص است.
- [ ] تغییرات uncommitted بررسی شده‌اند.
- [ ] تست‌های مرتبط شناسایی شده‌اند.
- [ ] وابستگی به شبکه/Provider/Drive مشخص شده است.

## C. Evidence Gate
برای هر ادعای فنی مهم:
- [ ] منبع معتبر مشخص است.
- [ ] تاریخ/نسخهٔ منبع مشخص است.
- [ ] ادعا دقیقاً با منبع سازگار است.
- [ ] در صورت امکان با test/fixture تأیید شده است.
- [ ] اگر تأیید نشده، برچسب UNVERIFIED دارد و کدنویسی متوقف است.

## D. قبل از Pull Request
- [ ] Change Record ایجاد شده است.
- [ ] دلیل تغییر و شواهد در آن ثبت شده است.
- [ ] تست‌ها اجرا و خروجی ثبت شده‌اند.
- [ ] اثرات جانبی و migration مشخص شده‌اند.
- [ ] هیچ secret یا credential وارد diff نشده است.
- [ ] PR template کامل شده است.

## E. پایان session
- [ ] تغییرات در branch ثبت شده‌اند.
- [ ] Ledger به‌روزرسانی شده است.
- [ ] وضعیت unresolved/blocked ثبت شده است.
- [ ] اگر Drive در دسترس بوده، فایل‌های مرجع طبق سیاست sync ثبت شده‌اند؛ اگر نبوده، ادعای sync نشده است.
