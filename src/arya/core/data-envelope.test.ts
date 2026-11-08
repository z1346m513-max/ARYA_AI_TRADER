import { describe, expect, it } from "vitest";

import {
  combineMeta,
  demo,
  envelope,
  isReal,
  unavailable,
  withFreshness,
} from "@/arya/core/data-envelope";

describe("data envelope", () => {
  it("stamps provenance and clamps quality", () => {
    const env = envelope([1, 2], {
      source: "TestProvider",
      providerId: "test",
      status: "LIVE",
      quality: 5,
      timestamp: 1000,
    });
    expect(env.meta.quality).toBe(1);
    expect(env.meta.timestamp).toBe(1000);
    expect(isReal(env)).toBe(true);
  });

  it("marks demo payloads as not real", () => {
    const env = demo({ price: 10 }, "MockProvider", "mock", 500);
    expect(env.meta.status).toBe("DEMO");
    expect(isReal(env)).toBe(false);
  });

  it("returns UNAVAILABLE with a reason and zero quality", () => {
    const env = unavailable<number[]>([], "CodalProvider", "codal", "not implemented");
    expect(env.meta.status).toBe("UNAVAILABLE");
    expect(env.meta.quality).toBe(0);
    expect(env.meta.reason).toBe("not implemented");
    expect(isReal(env)).toBe(false);
  });

  it("downgrades LIVE data to STALE past the age limit", () => {
    const env = envelope(1, { source: "S", providerId: "s", status: "LIVE", timestamp: 0 });
    expect(withFreshness(env, 1000, 500).meta.status).toBe("LIVE");
    const stale = withFreshness(env, 1000, 5000);
    expect(stale.meta.status).toBe("STALE");
    expect(stale.meta.quality).toBeLessThan(env.meta.quality);
  });

  it("never ages DEMO data into something real", () => {
    const env = demo(1, "MockProvider", "mock", 0);
    expect(withFreshness(env, 1, 999_999).meta.status).toBe("DEMO");
  });

  it("combines provenance down to the weakest input", () => {
    const meta = combineMeta(
      [
        envelope(1, { source: "A", providerId: "a", status: "LIVE", quality: 1, timestamp: 10 }).meta,
        demo(2, "MockProvider", "mock", 5).meta,
      ],
      "ScoringEngine",
      "scoring",
    );
    expect(meta.status).toBe("DEMO");
    expect(meta.quality).toBe(0.5);
    expect(meta.timestamp).toBe(5);
  });

  it("treats an empty input set as UNAVAILABLE", () => {
    expect(combineMeta([], "X", "x").status).toBe("UNAVAILABLE");
  });
});
