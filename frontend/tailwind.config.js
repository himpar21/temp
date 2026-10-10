/** @type {import('tailwindcss').Config} */
export default {
  darkMode: "class",
  content: ["./index.html", "./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        ink: "var(--color-ink)",
        paper: "var(--color-paper)",
        slate: "var(--color-slate)",
        line: "var(--color-line)",
        surface: "var(--color-surface)",
        accent: "var(--color-accent)",
        "accent-soft": "var(--color-accent-soft)",
        pass: "var(--color-pass)",
        fail: "var(--color-fail)",
        warn: "var(--color-warn)",
      },
      fontFamily: {
        sans: ["'IBM Plex Sans'", "system-ui", "sans-serif"],
        mono: ["'IBM Plex Mono'", "ui-monospace", "monospace"],
      },
      borderRadius: {
        DEFAULT: "4px",
      },
    },
  },
  plugins: [],
};
