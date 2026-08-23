// Loads web/app.js in a stubbed browser environment.
// A TDZ/ReferenceError in the const state literal (or any load-time error)
// throws during require() and fails the smoke with LOAD_ERROR.
"use strict";

const elements = {};

function makeEl() {
  return {
    value: "",
    textContent: "",
    title: "",
    checked: false,
    disabled: false,
    dataset: {},
    style: {},
    classList: { add() {}, remove() {}, toggle() {} },
    options: [],
    _html: "",
    set innerHTML(v) { this._html = v; },
    get innerHTML() { return this._html; },
    appendChild() {},
    addEventListener() {},
    querySelector() { return makeEl(); },
    querySelectorAll() { return []; },
  };
}

const loadErrors = [];
const originalError = console.error;
console.error = (...args) => {
  loadErrors.push(args.map(String).join(" "));
  originalError(...args);
};

global.document = {
  documentElement: { lang: "ru" },
  body: { classList: { add() {}, remove() {} } },
  getElementById(id) {
    if (!elements[id]) elements[id] = makeEl();
    return elements[id];
  },
  querySelectorAll() { return []; },
  createElement() { return makeEl(); },
};
global.window = global;
global.location = { search: "" };
global.localStorage = { getItem: () => null, setItem: () => {} };
global.fetch = async () => ({
  ok: true,
  json: async () => ({ voices: [], roles: [], presets: {}, files: [] }),
});
global.URLSearchParams = class {
  constructor() {}
  get() { return null; }
};
global.URL = { createObjectURL: () => "blob:x" };
global.Blob = function () {};
global.Audio = class {
  play() { return Promise.resolve(); }
};
global.atob = (s) => Buffer.from(s, "base64").toString("latin1");

try {
  require("../web/app.js");
} catch (err) {
  console.error("LOAD_ERROR " + (err && err.stack ? err.stack : err));
  process.exit(1);
}

setTimeout(() => {
  const fatal = loadErrors.filter(e => /ReferenceError|TypeError/.test(e));
  if (fatal.length) {
    console.error("RUNTIME_ERROR " + fatal[0]);
    process.exit(1);
  }
  console.log("STATE_OK");
  process.exit(0);
}, 150);