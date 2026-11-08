/** Browser IndexedDB store for manually uploaded daily market-watch snapshots. */
import type { DailySnapshot } from "@/arya/providers/marketwatch-import";

const DB = "arya-daily";
const STORE = "snapshots";

function open(): Promise<IDBDatabase> {
  return new Promise((resolve, reject) => {
    const req = indexedDB.open(DB, 1);
    req.onupgradeneeded = () => req.result.createObjectStore(STORE, { keyPath: "jalali" });
    req.onsuccess = () => resolve(req.result);
    req.onerror = () => reject(req.error);
  });
}

function run<T>(mode: IDBTransactionMode, fn: (s: IDBObjectStore) => IDBRequest<T>): Promise<T> {
  return open().then((db) => new Promise<T>((resolve, reject) => {
    const req = fn(db.transaction(STORE, mode).objectStore(STORE));
    req.onsuccess = () => resolve(req.result);
    req.onerror = () => reject(req.error);
  }));
}

const listeners = new Set<() => void>();
export const onSnapshotsChange = (fn: () => void) => (listeners.add(fn), () => void listeners.delete(fn));

export async function saveSnapshot(s: DailySnapshot) {
  await run("readwrite", (st) => st.put(s));
  listeners.forEach((l) => l());
}
export const listSnapshots = () => run<DailySnapshot[]>("readonly", (st) => st.getAll());
export async function deleteSnapshot(jalali: string) {
  await run("readwrite", (st) => st.delete(jalali));
  listeners.forEach((l) => l());
}
