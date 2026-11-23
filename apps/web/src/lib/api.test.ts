import { describe, expect, it } from "vitest"

import { apiUrl } from "./api"

describe("apiUrl", () => {
  it("keeps a relative path when the base is empty", () => {
    expect(apiUrl("/v1/orders", "")).toBe("/v1/orders")
  })

  it("prefixes the API origin and drops a trailing slash", () => {
    expect(apiUrl("/v1/orders", "http://127.0.0.1:8000/")).toBe(
      "http://127.0.0.1:8000/v1/orders",
    )
  })
})
