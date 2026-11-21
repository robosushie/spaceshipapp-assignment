import { describe, expect, it } from "vitest"

import { money, statusLabel } from "./format"

describe("statusLabel", () => {
  it("spells in transit as two words", () => {
    expect(statusLabel("in_transit")).toBe("in transit")
    expect(statusLabel("delivered")).toBe("delivered")
  })
})

describe("money", () => {
  it("formats a decimal string as dollars", () => {
    expect(money("26.22")).toBe("$26.22")
  })
})
