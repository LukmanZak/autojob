import test from "node:test";
import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";

const html = await readFile(new URL("../index.html", import.meta.url), "utf8").catch(() => "");
const cta = await readFile(new URL("../compositions/components/cta-lockup.html", import.meta.url), "utf8").catch(() => "");

test("composition is a registered 10-second vertical Click Tools stage", () => {
  assert.match(html, /data-composition-id=["']click-tools["']/);
  assert.match(html, /data-duration=["']10(?:\.0)?["']/);
  assert.match(html, /data-width=["']1080["']/);
  assert.match(html, /data-height=["']1920["']/);
  assert.match(html, /window\.__timelines\[["']click-tools["']\]\s*=\s*tl/);
});

test("closing sub-composition fits its 2.1-second host slot", () => {
  const host = html.match(/id=["']cta-lockup["'][\s\S]*?data-start=["']([\d.]+)["'][\s\S]*?data-duration=["']([\d.]+)["']/);
  const clip = cta.match(/id=["']cta-lockup-clip["'][\s\S]*?data-duration=["']([\d.]+)["']/);
  assert.ok(host, "Missing CTA host timing");
  assert.ok(clip, "Missing CTA sub-composition timing");
  assert.equal(Number(host[1]) + Number(host[2]), 10);
  assert.equal(Number(clip[1]), Number(host[2]));
});

test("composition contains every approved English message", () => {
  for (const text of [
    "CLICK TOOLS",
    "Tools for the way you work.",
    "Automate the busywork.",
    "AI for everyday life.",
    "Built for business",
    "enterprise.",
    "Create visuals with AI.",
    "Automation. AI. Creativity.",
    "Follow for smarter tools.",
  ]) {
    assert.ok(html.includes(text), `Missing on-screen copy: ${text}`);
  }
});

test("composition does not use infinite GSAP repeats", () => {
  assert.doesNotMatch(html, /repeat\s*:\s*-1/);
});
