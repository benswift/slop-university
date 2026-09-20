import { describe, expect, it } from "vitest";
import { type Candidate, validateCatalogue } from "./catalogue";

const feed = (code = "SLOP2713") => ({
  schemaVersion: 1,
  canonicalUrl: `https://courses.slop.university/${code}/`,
  course: {
    code,
    title: "Small Machines for Large Puddles",
    session: "Semester 2",
    year: 2027,
    level: Number(code[4]),
    startDate: "2027-07-26",
    endDate: "2027-10-29",
    description:
      "A focused course for students who want to build, observe and explain tiny machines working in inconveniently large puddles.",
    tags: ["machines", "puddles"],
    learningOutcomes: [],
  },
  timezone: "Australia/Canberra",
  nodes: [],
  edges: [],
});

const candidate = (code = "SLOP2713", overrides: Partial<Candidate> = {}): Candidate => ({
  apiUrl: `https://example.test/${code}/api/index.json`,
  sourceUrl: `https://example.test/${code}`,
  feed: feed(code),
  ...overrides,
});

describe("catalogue contract", () => {
  it("accepts a valid feed", () => {
    const { entries, rejected } = validateCatalogue([candidate()]);
    expect(rejected).toEqual([]);
    expect(entries).toHaveLength(1);
  });

  it("accepts the timezone the course API emits", () => {
    expect(validateCatalogue([candidate()]).entries[0]?.feed.timezone).toBe("Australia/Canberra");
  });

  it("keeps the source and etag alongside the feed", () => {
    const { entries } = validateCatalogue([candidate("SLOP2713", { etag: '"abc"' })]);
    expect(entries[0]?.sourceUrl).toBe("https://example.test/SLOP2713");
    expect(entries[0]?.etag).toBe('"abc"');
  });

  it("rejects collisions with reroll guidance, keeping the first claimant", () => {
    const { entries, rejected } = validateCatalogue([candidate(), candidate()]);
    expect(entries).toHaveLength(1);
    expect(rejected[0]?.reason).toMatch(/reroll the last three digits/);
  });

  it("rejects a level mismatch", () => {
    const broken = candidate();
    broken.feed = { ...feed(), course: { ...feed().course, level: 3 } };
    expect(validateCatalogue([broken]).rejected[0]?.reason).toMatch(/level does not match/);
  });

  it("keeps the good feeds when one is malformed", () => {
    const broken = candidate("SLOP3001");
    broken.feed = {
      ...feed("SLOP3001"),
      course: { ...feed("SLOP3001").course, description: "too short" },
    };
    const { entries, rejected } = validateCatalogue([candidate(), broken]);
    expect(entries).toHaveLength(1);
    expect(rejected).toHaveLength(1);
  });
});
