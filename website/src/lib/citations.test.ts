import { describe, expect, it } from "vitest";
import { hIndex } from "./citations";

// The one piece of arithmetic on a profile page that isn't a count or a sum ---
// and the one a reader is most likely to check by hand against the "cited by"
// lists the same graph renders.
describe("hIndex", () => {
  it("is zero for a researcher whose outputs are all uncited", () => {
    expect(hIndex([])).toBe(0);
    expect(hIndex([0, 0, 0])).toBe(0);
  });

  it("is the largest h with h outputs cited at least h times", () => {
    expect(hIndex([1])).toBe(1);
    expect(hIndex([5, 4, 3, 2, 1])).toBe(3);
    expect(hIndex([3, 3, 3])).toBe(3);
    expect(hIndex([10, 1, 1])).toBe(1);
  });

  it("does not depend on the order the counts arrive in", () => {
    expect(hIndex([1, 5, 2, 4, 3])).toBe(hIndex([5, 4, 3, 2, 1]));
  });

  it("is capped by the number of outputs, however heavily cited", () => {
    expect(hIndex([99, 99])).toBe(2);
  });
});
