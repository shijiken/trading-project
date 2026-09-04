import "@testing-library/jest-dom/vitest";

// jsdom reports 0x0 for every element, so Recharts' ResponsiveContainer never
// measures a usable size and skips rendering its inner SVG (Brush included).
// Give every element a fixed, non-zero box so charts fully render in tests.
Element.prototype.getBoundingClientRect = () => ({
  width: 800,
  height: 400,
  top: 0,
  left: 0,
  bottom: 400,
  right: 800,
  x: 0,
  y: 0,
  toJSON() {},
});

// jsdom has no ResizeObserver, which Recharts' ResponsiveContainer relies on
// to learn its size — report the (now non-zero) size immediately on observe.
if (!global.ResizeObserver) {
  global.ResizeObserver = class {
    constructor(callback) {
      this.callback = callback;
    }
    observe(target) {
      this.callback([{ target, contentRect: target.getBoundingClientRect() }]);
    }
    unobserve() {}
    disconnect() {}
  };
}

