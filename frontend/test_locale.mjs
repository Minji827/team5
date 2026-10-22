import test from "node:test";
import assert from "node:assert/strict";
import { resources, translate } from "./src/locale.js";

test("all four languages have matching keys and substitution parameters", () => {
  const placeholders = (text) => [...text.matchAll(/\{(\w+)\}/g)].map((match) => match[1]).sort();
  for (const [locale, copy] of Object.entries(resources)) {
    assert.deepEqual(Object.keys(copy).sort(), Object.keys(resources.ko).sort());
    for (const [key, value] of Object.entries(copy)) {
      assert.ok(value.trim(), `${locale}:${key}`);
      assert.deepEqual(placeholders(value), placeholders(resources.ko[key]), `${locale}:${key}`);
    }
  }
});
test("category aliases and estimated times translate without changing category IDs", () => {
  assert.equal(translate("en", "카페/디저트"), "Café & dessert");
  assert.equal(translate("ja", "카페·디저트"), "カフェ・スイーツ");
  assert.equal(translate("zh-TW", "식당"), "餐廳");
  assert.equal(translate("zh-TW", "walkTime", { n: 10 }), "步行約10分鐘");
  assert.equal(translate("en", "placeCount", { count: 1 }), "1 stop");
  assert.equal(translate("ja", translate("en", "swapBudget")), resources.ja.swapBudget);
});
