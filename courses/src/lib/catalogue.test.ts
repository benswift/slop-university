import { describe, expect, it } from "vitest";
import { validateCatalogue } from "./catalogue";

const feed = (code = "SLOP2713") => ({
  schemaVersion: 1,
  canonicalUrl: `https://courses.slop.university/${code}/`,
  course: {
    code,
    title: "Small Machines for Large Puddles",
    session: "Semester 2",
    year: 2027,
    level: 2,
    startDate: "2027-07-26",
    endDate: "2027-10-29",
    description:
      "A focused course for students who want to build, observe and explain tiny machines working in inconveniently large puddles.",
    tags: ["machines", "puddles"],
    learningOutcomes: [],
  },
  nodes: [],
  edges: [],
});

describe("catalogue contract", () => {
  it("accepts a valid feed", () => expect(validateCatalogue([feed()])).toHaveLength(1));
  it("rejects collisions with reroll guidance", () =>
    expect(() => validateCatalogue([feed(), feed()])).toThrow(/reroll the last three digits/));
  it("rejects a level mismatch", () =>
    expect(() =>
      validateCatalogue([{ ...feed(), course: { ...feed().course, level: 3 } }]),
    ).toThrow(/level does not match/));
});
