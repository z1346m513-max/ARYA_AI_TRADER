/**
 * داده‌های نمونه‌ی داشبورد، هم‌راستا با پایپ‌لاین مخزن ARYA_AI_TRADER:
 * Providers → Storage → Indicator Engine → Analysis → Scoring → AI Decision →
 * Risk Manager → Recommendation Engine → Dashboard
 */

export type Candle = {
  t: number;
  label: string;
  open: number;
  high: number;
  low: number;
  close: number;
  volume: number;
  ma20: number;
  ma50: number;
  rsi: number;
};

function mulberry32(seed: number) {
  return () => {
    seed |= 0;
    seed = (seed + 0x6d2b79f5) | 0;
    let t = Math.imul(seed ^ (seed >>> 15), 1 | seed);
    t = (t + Math.imul(t ^ (t >>> 7), 61 | t)) ^ t;
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
  };
}

const MONTHS = ["مرداد", "شهریور", "مهر", "آبان", "آذر", "دی"];

/** شبیه‌سازی MockProvider مخزن: قیمت قطعی و تکرارپذیر برای هر نماد. */
export function generateSeries(ticker: string, base = 4600, count = 120): Candle[] {
  const seed = [...ticker].reduce((a, c) => a + c.charCodeAt(0) * 31, 7);
  const rnd = mulberry32(seed);
  const closes: number[] = [];
  const out: Candle[] = [];
  let price = base;

  for (let i = 0; i < count; i++) {
    const drift = Math.sin(i / 11) * 0.006 + Math.sin(i / 29) * 0.004 + 0.0009;
    const shock = (rnd() - 0.5) * 0.022;
    const open = price;
    const close = Math.max(80, open * (1 + drift + shock));
    const high = Math.max(open, close) * (1 + rnd() * 0.008);
    const low = Math.min(open, close) * (1 - rnd() * 0.008);
    closes.push(close);

    const ma = (n: number) => {
      const s = closes.slice(Math.max(0, closes.length - n));
      return s.reduce((a, b) => a + b, 0) / s.length;
    };

    const window = closes.slice(-15);
    let gain = 0;
    let loss = 0;
    for (let k = 1; k < window.length; k++) {
      const d = (window[k] as number) - (window[k - 1] as number);
      if (d >= 0) gain += d;
      else loss -= d;
    }
    const rs = loss === 0 ? 100 : gain / loss;
    const rsi = window.length < 3 ? 50 : 100 - 100 / (1 + rs);

    out.push({
      t: i,
      label: MONTHS[Math.floor((i / count) * MONTHS.length)] ?? "",
      open: +open.toFixed(0),
      high: +high.toFixed(0),
      low: +low.toFixed(0),
      close: +close.toFixed(0),
      volume: +(rnd() * 40 + 8).toFixed(1),
      ma20: +ma(20).toFixed(0),
      ma50: +ma(50).toFixed(0),
      rsi: +rsi.toFixed(2),
    });
    price = close;
  }
  return out;
}

export const marketTickers = [
  { label: "شاخص کل", value: "2,145,435", change: "+1.35%", up: true },
  { label: "شپنا", value: "5,230", change: "+2.14%", up: true },
  { label: "شاخص هم وزن", value: "702,384", change: "+1.10%", up: true },
  { label: "دلار", value: "59,850", change: "-0.32%", up: false },
  { label: "طلا ۱۸", value: "3,450,000", change: "+0.85%", up: true },
  { label: "بیت کوین", value: "64,250", change: "+1.25%", up: true },
];

/** خروجی Scoring Engine: SectionScore ها با وزن پروفایل فعال. */
export const sectionScores = [
  { key: "technical", label: "تکنیکال", score: 82, tone: "bull" as const },
  { key: "fundamental", label: "بنیادی", score: 75, tone: "bull" as const },
  { key: "news", label: "خبر و احساسات", score: 70, tone: "bull" as const },
  { key: "codal", label: "کدال", score: 65, tone: "neutral" as const },
  { key: "smart_money", label: "اسمارت مانی", score: 85, tone: "bull" as const },
  { key: "risk", label: "ریسک", score: 60, tone: "neutral" as const },
  { key: "ai", label: "اعتماد AI", score: 80, tone: "bull" as const },
];

/** خروجی Recommendation Engine + Risk Manager. */
export const recommendation = {
  action: "خرید",
  confidence: 80,
  overallScore: 78,
  rows: [
    { label: "هدف کوتاه مدت", value: "5,800", delta: "+10.9%", up: true },
    { label: "هدف میان مدت", value: "6,450", delta: "+23.3%", up: true },
    { label: "حد ضرر", value: "4,850", delta: "-7.3%", up: false },
    { label: "ریسک به ریوارد", value: "1 : 2.5", delta: "", up: true },
  ],
  reasons: [
    "بخش «تکنیکال» سیگنال صعودی با قدرت 0.64 و اطمینان 0.81 می‌دهد.",
    "جریان پول هوشمند در ۵ جلسه‌ی اخیر مثبت و رو به افزایش است.",
    "امتیاز کلی (0.56) بالاتر از آستانه‌ی خرید موتور تصمیم است.",
  ],
};

export const watchlist = [
  { ticker: "شپنا", price: "5,230", change: "+2.14%", up: true },
  { ticker: "شتران", price: "4,125", change: "+1.23%", up: true },
  { ticker: "فملی", price: "8,730", change: "+0.91%", up: true },
  { ticker: "وبملت", price: "2,890", change: "-0.34%", up: false },
  { ticker: "خودرو", price: "3,220", change: "-1.05%", up: false },
  { ticker: "تتر", price: "59,850", change: "-0.32%", up: false },
  { ticker: "بیت کوین", price: "64,250", change: "+1.25%", up: true },
  { ticker: "اتریوم", price: "3,210", change: "+0.85%", up: true },
];

export const news = [
  { time: "10:15", tag: "کدال", tone: "info" as const, text: "افزایش سرمایه ۱۰۰٪ از محل سود انباشته" },
  { time: "09:45", tag: "کدال", tone: "info" as const, text: "گزارش ماهانه آذر ماه ۱۴۰۳ منتشر شد" },
  { time: "09:30", tag: "خبر", tone: "bear" as const, text: "رشد ۱۵ درصدی تولید نسبت به ماه قبل" },
  { time: "09:10", tag: "تحلیل", tone: "accent" as const, text: "تحلیل وضعیت صنعت پالایشگاهی" },
];

export const breadth = [
  { label: "مثبت", value: 325, color: "var(--bull)" },
  { label: "منفی", value: 180, color: "var(--bear)" },
  { label: "بدون تغییر", value: 95, color: "var(--neutral)" },
];

export const indicatorPanel = [
  { name: "MA (20/50)", state: "تقاطع صعودی", tone: "bull" as const },
  { name: "RSI (14)", state: "62.35 — خنثی رو به قدرت", tone: "neutral" as const },
  { name: "MACD (12/26/9)", state: "هیستوگرام مثبت", tone: "bull" as const },
  { name: "Bollinger (20,2)", state: "فشردگی در حال باز شدن", tone: "neutral" as const },
  { name: "OBV", state: "واگرایی مثبت با قیمت", tone: "bull" as const },
];

/** لایه‌های معماری مخزن (docs/architecture). */
export const architecture: {
  id: string;
  title: string;
  accent: string;
  groups: { title?: string; items: string[] }[];
}[] = [
  {
    id: "1",
    title: "۱. منابع داده",
    accent: "var(--chart-5)",
    groups: [{ items: ["بورس (TSETMC)", "کدال (Codal.ir)", "اخبار و رسانه‌ها", "ارز دیجیتال", "فارکس", "تقویم اقتصادی"] }],
  },
  {
    id: "2",
    title: "۲. لایه Provider",
    accent: "var(--chart-4)",
    groups: [{ items: ["Market Provider", "Codal Provider", "News Provider", "Crypto Provider", "Forex Provider", "Macro Provider"] }],
  },
  {
    id: "3",
    title: "۳. لایه داده",
    accent: "var(--chart-5)",
    groups: [{ items: ["Data Manager", "Data Cache (Memory)", "Database (SQLite)", "File Storage"] }],
  },
  {
    id: "4",
    title: "۴. موتور تحلیل",
    accent: "var(--bull)",
    groups: [
      { title: "Technical / Smart Money / Fundamental", items: ["Indicators", "Patterns", "Multi Timeframe", "BOS / CHOCH", "Order Blocks", "FVG / Liquidity", "Financial Ratios", "Valuation", "Cash Flow"] },
      { title: "Scoring & Weighting Engine", items: ["Technical Score", "Fundamental Score", "News Score", "Smart Money Score", "Codal Score", "Risk Score"] },
      { title: "AI Decision Engine", items: ["Reasoning", "Prediction", "Confidence", "Explanation", "Scenario"] },
      { title: "Recommendation Engine", items: ["Buy / Sell / Hold", "Targets", "Stop Loss", "Position Size", "Risk-Reward"] },
    ],
  },
  {
    id: "5",
    title: "۵. ریسک و پرتفوی",
    accent: "var(--chart-4)",
    groups: [
      { title: "Risk Manager", items: ["Position Sizing", "Stop Loss", "Take Profit", "Risk Metrics"] },
      { title: "Portfolio Manager", items: ["Holdings", "Performance", "Allocation", "Reports"] },
    ],
  },
  {
    id: "6",
    title: "۶. لایه اپلیکیشن",
    accent: "var(--primary)",
    groups: [{ items: ["API Layer", "Service Layer", "Task Scheduler", "Notification Service", "Export Service"] }],
  },
  {
    id: "7",
    title: "۷. لایه نمایش",
    accent: "var(--chart-4)",
    groups: [{ items: ["Dashboard", "Chart & Analysis", "Watchlist", "AI Assistant", "Backtest", "Reports", "Settings"] }],
  },
];

export const infrastructure = ["Logging", "Monitoring", "Error Tracking", "Backup Service", "Auto Update", "Security"];