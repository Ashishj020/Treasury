/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        ink: {
          0: "#07090D",
          1: "#0B0F14",
          2: "#10151C",
          3: "#161C26",
        },
        mist: {
          50: "#F5F7FA",
          200: "#C5CDD8",
          400: "#8B95A5",
          600: "#596273",
        },
        cyan: { DEFAULT: "#22D3EE", dim: "#155E75" },
        pink: { DEFAULT: "#F472B6" },
        emerald: { DEFAULT: "#34D399" },
        indigo: { DEFAULT: "#6366F1" },
        violet: { DEFAULT: "#8B5CF6" },
        orchid: { DEFAULT: "#C084FC" },
        plum: { DEFAULT: "#7A3E65" },
      },
      fontFamily: {
        serif: ['"Fraunces"', "Georgia", "serif"],
        sans: ['"IBM Plex Sans"', "system-ui", "sans-serif"],
        mono: ['"IBM Plex Mono"', "ui-monospace", "monospace"],
      },
      boxShadow: {
        glass: "0 10px 40px rgba(0,0,0,0.35)",
      },
    },
  },
  plugins: [],
};
