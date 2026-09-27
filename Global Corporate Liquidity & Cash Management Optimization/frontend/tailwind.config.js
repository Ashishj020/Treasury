/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        bg: "#07090D",
        surface: "#0B0F14",
        elevated: "#10151C",
        ink: "#F5F7FA",
        mute: "#8B95A5",
        faint: "#596273",
        cyan: "#22D3EE",
        emerald: "#34D399",
        mint: "#A7F3D0",
        pink: "#F472B6",
        violet: "#8B5CF6",
        indigo: "#6366F1",
        plum: "#581C4D",
        dewberry: "#7A3E65",
        danger: "#FB7185",
      },
      fontFamily: {
        sans: ["Manrope", "IBM Plex Sans", "system-ui", "sans-serif"],
        mono: ["IBM Plex Mono", "ui-monospace", "monospace"],
        display: ["Syne", "Manrope", "sans-serif"],
      },
      boxShadow: {
        glow: "0 0 40px rgba(34, 211, 238, 0.08)",
      },
    },
  },
  plugins: [],
};
