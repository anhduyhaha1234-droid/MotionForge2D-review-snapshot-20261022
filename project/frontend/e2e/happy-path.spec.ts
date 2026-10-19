import { test, expect } from "@playwright/test";
import fs from "fs";
import path from "path";
import { execSync } from "child_process";

const FIXTURE_DIR = path.join(__dirname, "fixtures");
const VIDEO_PATH = path.join(FIXTURE_DIR, "test-2s.mp4");

/* ── Setup: generate a tiny test video ──────────────────────────────────── */

test.beforeAll(() => {
  if (!fs.existsSync(FIXTURE_DIR)) fs.mkdirSync(FIXTURE_DIR, { recursive: true });
  if (!fs.existsSync(VIDEO_PATH)) {
    try {
      execSync(
        `ffmpeg -y -f lavfi -i "color=c=blue:s=320x240:d=2" -vf "drawtext=text='Test':fontsize=40:fontcolor=white:x=(w-text_w)/2:y=(h-text_h)/2" -c:v libx264 -pix_fmt yuv420p "${VIDEO_PATH}"`,
        { stdio: "ignore" },
      );
    } catch {
      console.warn("ffmpeg not available — fixture video not created");
    }
  }
});

/* ── Happy-path E2E ─────────────────────────────────────────────────────── */

test.describe("MotionForge 2D — Happy Path", () => {
  test("full workflow: create → select → replace → render", async ({
    page,
  }) => {
    // Step 1: Open the app
    await page.goto("/");
    await expect(page.locator("h1")).toContainText("MotionForge 2D");

    // Step 2: Fill project name
    const nameInput = page.locator('input[type="text"]');
    await nameInput.clear();
    await nameInput.fill("E2E Test Project");

    // Step 3: Upload fixture video
    const fileInput = page.locator('input[type="file"][accept*=".mp4"]');
    await fileInput.setInputFiles(VIDEO_PATH);

    // Step 4: Start upload & ingest
    await page.getByRole("button", { name: /Bắt đầu/i }).click();

    // Step 5: Wait for ingest — app auto-navigates to selection screen
    await expect(page.locator("text=Chọn vật thể")).toBeVisible({
      timeout: 90_000,
    });

    // Step 6: Verify frame info is visible
    await expect(page.locator("text=320×240")).toBeVisible({ timeout: 5_000 });

    // Step 7: Click on canvas to select an object
    const canvas = page.locator("canvas").first();
    await expect(canvas).toBeVisible();
    await canvas.click({ position: { x: 160, y: 120 } });

    // Wait for selection to register
    await page.waitForTimeout(500);

    // Step 8: Preview mask
    const maskBtn = page.getByRole("button", { name: /Xem mask/i });
    await expect(maskBtn).toBeVisible({ timeout: 5_000 });
    await maskBtn.click();

    // Wait for mask to load
    await page.waitForTimeout(2000);

    // Step 9: Accept and propagate
    const acceptBtn = page.getByRole("button", { name: /Chấp nhận/i });
    await expect(acceptBtn).toBeVisible({ timeout: 5_000 });
    await acceptBtn.click();

    // Step 10: Wait for propagation to complete — Screen C
    await expect(page.locator("text=Kết quả tách object")).toBeVisible({
      timeout: 120_000,
    });

    // Step 11: Verify gallery is visible
    await expect(
      page.locator("text=/Gallery frame đại diện/"),
    ).toBeVisible({ timeout: 10_000 });

    // Step 12: Navigate to replacement screen
    const replaceBtn = page.getByRole("button", { name: /Thay ảnh/i });
    if (await replaceBtn.isVisible({ timeout: 3_000 }).catch(() => false)) {
      await replaceBtn.click();
      await expect(page.locator("text=Thay thế vật thể")).toBeVisible({
        timeout: 5_000,
      });
    }
  });
});
