# معماری چندایجنتی ARYA + مغز دوم (Second Brain)

هدف: جداسازی خدمات به‌صورت **ایجنت‌های مستقل**، با یک **حافظه مرکزی** که دانش را نگه می‌دارد، دسته‌بندی می‌کند و در اختیار بقیه قرار می‌دهد. در صورت نیاز، داده روی دیسک (درایو) پایدار می‌شود.

---

## ۱) دیاگرام کلی

```mermaid
flowchart TB
  subgraph External["منابع خارجی"]
    TSETMC[TSETMC CDN]
    CODAL[کدال]
    WEB[سایت‌های مشابه / اخبار / GitHub]
    USER[کاربر / ورود دستی]
  end

  subgraph Agents["ایجنت‌های خدمت"]
    A1[Agent Market\nقیمت / صف / جزئیات]
    A2[Agent Flow\nحقیقی-حقوقی / سهامدار]
    A3[Agent Codal\nAPI یا دستی]
    A4[Agent Strategy\nاندیکاتور و اسکن]
    A5[Agent Research\nجست‌وجوی وب/مشابه]
    A6[Agent Research2\nالگو از پروژه‌های مشابه]
    A7[Agent Analyst\nامتیاز و پیشنهاد]
    A8[Agent Risk\nریسک و اندازه پوزیشن]
  end

  subgraph Brain["مغز دوم — Second Brain"]
    MEM[حافظه کاری Working Memory]
    CAT[دسته‌بند / ایندکس]
    EPIS[حافظه رویدادی Episodic]
    KNOW[دانش پایدار Knowledge]
    DISK[ذخیره فیزیکی\ndata/second_brain/]
  end

  TSETMC --> A1
  TSETMC --> A2
  CODAL --> A3
  USER --> A3
  WEB --> A5
  WEB --> A6

  A1 -->|quotes, ohlcv| MEM
  A2 -->|client_type, holders| MEM
  A3 -->|letters, events| MEM
  A5 -->|snippets, links| MEM
  A6 -->|patterns, APIs| MEM

  MEM --> CAT
  CAT --> EPIS
  CAT --> KNOW
  EPIS --> DISK
  KNOW --> DISK

  MEM --> A4
  MEM --> A7
  KNOW --> A7
  EPIS --> A7
  A7 --> A8
  A4 -->|scan hits| MEM
  A8 -->|risk notes| MEM
```

---

## ۲) دیاگرام توالی یک چرخه تحلیل

```mermaid
sequenceDiagram
  participant U as کاربر
  participant Orch as Orchestrator
  participant SB as Second Brain
  participant M as Agent Market
  participant F as Agent Flow
  participant C as Agent Codal
  participant R as Agent Research
  participant S as Agent Strategy
  participant A as Agent Analyst

  U->>Orch: analyze فولاد
  Orch->>SB: recall(ticker=فولاد)
  SB-->>Orch: context قبلی

  par به‌روزرسانی موازی
    Orch->>M: refresh OHLCV/detail
    M->>SB: store(market)
    Orch->>F: refresh client_type
    F->>SB: store(flow)
    Orch->>C: fetch letters یا manual
    C->>SB: store(codal)
    Orch->>R: search similar insights
    R->>SB: store(research)
  end

  Orch->>S: evaluate strategies
  S->>SB: store(scan_hits)
  Orch->>A: score + decide
  A->>SB: store(recommendation)
  A-->>U: پیشنهاد + دلایل
```

---

## ۳) نقش ایجنت‌ها

| ایجنت | مسئولیت | ورودی | خروجی به مغز دوم |
|--------|---------|--------|-------------------|
| **Market** | قیمت، OHLCV، جزئیات نماد، صف | TSETMC | `market/*` |
| **Flow** | حقیقی/حقوقی، سهامداران | TSETMC | `flow/*` |
| **Codal** | اطلاعیه API یا دستی | کدال / کاربر | `codal/*` |
| **Strategy** | قوانین اندیکاتور + اسکن | OHLCV از حافظه | `strategy/*` |
| **Research** | جست‌وجوی سایت‌های مرتبط، نکات مفید | وب | `research/web/*` |
| **Research2** | الگو از پروژه‌های مشابه (GitHub و …) | وب/GitHub | `research/peers/*` |
| **Analyst** | ترکیب بخش‌ها، امتیاز، پیشنهاد | حافظه | `analysis/*` |
| **Risk** | حد ضرر، اندازه پوزیشن | تحلیل | `risk/*` |
| **Orchestrator** | زمان‌بندی و ترتیب فراخوانی | کاربر | — |

---

## ۴) مغز دوم (Second Brain)

### لایه‌ها

1. **Working Memory** — دادهٔ جلسه جاری (در RAM + فایل موقت)
2. **Episodic** — رویدادهای زمانی (تحلیل دیروز فولاد، اسکن استراتژی X)
3. **Knowledge** — دانش پایدار دسته‌بندی‌شده (نگاشت نماد، قوانین، الگوهای Peer)
4. **Disk** — `data/second_brain/` برای بقا بعد از بستن برنامه

### ساختار دیسک پیشنهادی

```text
data/second_brain/
  working/           # وضعیت آخرین جلسه
  episodic/          # YYYY-MM-DD/*.json
  knowledge/
    symbols/         # per-ticker summaries
    strategies/      # نتایج اسکن ذخیره‌شده
    research/        # یافته‌های وب دسته‌بندی‌شده
    peers/           # الگوهای پروژه‌های مشابه
  index.json         # ایندکس سبک برای جست‌وجو
```

### قرارداد پیام به حافظه

```json
{
  "agent": "market",
  "kind": "instrument_detail",
  "ticker": "فولاد",
  "ts": "2026-10-06T19:00:00Z",
  "tags": ["tsetmc", "eps", "pe"],
  "payload": { },
  "ttl_hours": 24
}
```

مغز دوم:
- ذخیره می‌کند
- بر اساس `kind` و `tags` دسته‌بندی می‌کند
- به Analyst / Strategy فقط **خلاصهٔ مرتبط** می‌دهد (نه کل وب)

---

## ۵) ایجنت‌های جست‌وجو (Research)

وظیفه: پیدا کردن اطلاعات **مفید و مرتبط با بورس ایران**، نه کپی بی‌هدف.

منابع نمونه:
- مستندات endpointهای TSETMC / کدال
- پروژه‌های GitHub مشابه (pytse-client، 5j9/tsetmc، …)
- اخبار/تحلیل عمومی (با برچسب منبع و تاریخ)

خروجی اجباری:
- `summary` کوتاه فارسی
- `source_url`
- `relevance` (0–1)
- `tags`
- ارسال به Second Brain با `kind=research_note`

Analyst **مستقیم** به وب نمی‌رود؛ فقط از حافظه می‌خواند.

---

## ۶) قوانین طراحی

1. هیچ ایجنتی state بلندمدت خودش را پنهان نگه ندارد → همه چیز از طریق مغز دوم.
2. نوشتن روی دیسک برای دادهٔ > جلسه یا قابل ممیزی (کدال دستی، توصیه، پژوهش).
3. به‌روزرسانی: Orchestrator می‌تواند زمان‌بندی کند (مثلاً هر روز Market+Flow).
4. P0 Symbol Master و Binaryها همچنان تحت کنترل کیفیت قبلی‌اند.
5. محدوده بازار: فقط بورس ایران.

---

## ۷) نقشه پیاده‌سازی کد

| مسیر | نقش |
|------|-----|
| `src/arya/agents/base.py` | قرارداد ایجنت |
| `src/arya/agents/second_brain.py` | حافظه + دیسک |
| `src/arya/agents/orchestrator.py` | هماهنگی |
| `src/arya/agents/research_agent.py` | جست‌وجو و ارسال به حافظه |
| `data/second_brain/` | مخزن فیزیکی |

CLI پیشنهادی بعدی:
```text
arya brain status
arya brain recall --ticker فولاد
arya research run --query "افزایش سرمایه فولاد"
```
