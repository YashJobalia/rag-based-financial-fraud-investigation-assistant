import { test, expect } from "@playwright/test";
import { readFileSync } from "node:fs";

test("case to citations, retrieval, and read-only review boundary", async ({
  page,
}) => {
  const errors: string[] = [];
  page.on("pageerror", (error) => errors.push(error.message));
  await page.goto("/");
  await expect(
    page.getByRole("heading", {
      name: "New device, new recipient",
      exact: true,
    }),
  ).toBeVisible();
  await expect(page.locator(".metrics").getByText("$8,000.00")).toBeVisible();
  await page.screenshot({
    path: "artifacts/case-overview.png",
    fullPage: true,
  });
  await page
    .getByRole("button", { name: "Prepare reference brief", exact: true })
    .click();
  await expect(
    page.getByText("Further investigation required", { exact: true }),
  ).toBeVisible();
  await expect(
    page.getByRole("heading", { name: "Legitimate explanations" }),
  ).toBeVisible();
  await page
    .getByTitle("Open evidence TX-001", { exact: true })
    .first()
    .click();
  await expect(page.getByRole("dialog")).toContainText("USD 4,800.00 transfer");
  await page.getByRole("button", { name: "Close evidence" }).click();
  await page
    .getByRole("button", { name: "Retrieved sources", exact: true })
    .click();
  await page.getByLabel("Search query").fill("replacement phone");
  await page
    .getByRole("button", { name: "Retrieve sources", exact: true })
    .click();
  await expect(
    page
      .locator(".source-card")
      .filter({ hasText: "Replacement phone verification" }),
  ).toBeVisible();
  await page.getByLabel("Search query").fill("orbital zeppelins");
  await page
    .getByRole("button", { name: "Retrieve sources", exact: true })
    .click();
  await expect(page.getByText(/No supporting passage found/)).toBeVisible();
  await page
    .getByRole("navigation", { name: "Case sections" })
    .getByRole("button", { name: "Analyst review" })
    .click();
  await expect(
    page.getByText(
      "The public demo cannot save decisions or run paid model calls.",
    ),
  ).toBeVisible();
  expect(errors).toEqual([]);
});

test("signed analyst session can persist a review", async ({ page }) => {
  const token = readFileSync(".local/analyst-token.txt", "utf8").trim();
  await page.goto("/");
  await page.getByRole("button", { name: /Demo explorer/ }).click();
  await page.getByLabel("Analyst session token").fill(token);
  await page.getByRole("button", { name: "Start analyst session" }).click();
  await expect(
    page.getByRole("button", { name: /Local analyst/ }),
  ).toBeVisible();
  await page
    .getByRole("button", { name: "Prepare reference brief", exact: true })
    .click();
  await page.getByRole("button", { name: "Review brief", exact: true }).click();
  await page
    .getByLabel("Reasoning and next checks")
    .fill(
      "Verify EV-001 through an established contact channel; confirm TX-001 and TX-002 separately.",
    );
  await page.getByRole("button", { name: "Save analyst review" }).click();
  await expect(page.getByRole("status")).toContainText("Review saved");
  await page.reload();
  await expect(
    page.getByRole("button", { name: /Demo explorer/ }),
  ).toBeVisible();
});

test("mobile case view has no horizontal overflow", async ({ page }) => {
  await page.setViewportSize({ width: 390, height: 844 });
  await page.goto("/");
  await expect(
    page.getByRole("heading", { name: "Evidence timeline" }),
  ).toBeVisible();
  expect(
    await page.evaluate(
      () => document.documentElement.scrollWidth <= window.innerWidth,
    ),
  ).toBeTruthy();
  await page.screenshot({ path: "artifacts/case-mobile.png", fullPage: true });
});
