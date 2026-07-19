import { describe, expect, it } from "vitest";

import {
  canIngest,
  canManageUsers,
  canRunEvals,
  canSeeApprovals,
  canSeeAudit,
  canSeeGovernance,
  canViewOrgWideInsights,
  roleLabel,
} from "./rbac";

describe("rbac helpers", () => {
  it("allows support and operations approvals visibility", () => {
    expect(canSeeApprovals(["support_user"])).toBe(true);
    expect(canSeeApprovals(["operations_user"])).toBe(true);
    expect(canSeeApprovals(["sales_user"])).toBe(false);
  });

  it("allows operations and admin audit visibility", () => {
    expect(canSeeAudit(["admin"])).toBe(true);
    expect(canSeeAudit(["operations_user"])).toBe(true);
    expect(canSeeAudit(["support_user"])).toBe(false);
  });

  it("limits governance and evals to admin", () => {
    expect(canSeeGovernance(["admin"])).toBe(true);
    expect(canSeeGovernance(["operations_user"])).toBe(false);
    expect(canRunEvals(["admin"])).toBe(true);
    expect(canRunEvals(["operations_user"])).toBe(false);
  });

  it("allows support and operations knowledge ingest", () => {
    expect(canIngest(["support_user"])).toBe(true);
    expect(canIngest(["operations_user"])).toBe(true);
    expect(canIngest(["sales_user"])).toBe(false);
  });

  it("limits user management to admin", () => {
    expect(canManageUsers(["admin"])).toBe(true);
    expect(canManageUsers(["operations_user"])).toBe(false);
  });

  it("labels roles for display", () => {
    expect(roleLabel("operations_user")).toBe("Operations");
    expect(canViewOrgWideInsights(["operations_user"])).toBe(true);
  });
});
