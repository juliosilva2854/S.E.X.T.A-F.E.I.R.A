/** @type {import('tailwindcss').Config} */
module.exports = {
  content: ["./src/**/*.{js,jsx,ts,tsx}", "./public/index.html"],
  theme: {
    extend: {
      colors: {
        bg: "#0A0A0A",
        surface: "#121212",
        surface2: "#1A1A1A",
        amber: {
          DEFAULT: "#F59E0B",
          hover: "#D97706",
        },
        zinc: {
          850: "#1F1F22",
        },
        ok: "#10B981",
        warn: "#F59E0B",
        err: "#EF4444",
      },
      fontFamily: {
        mono: ['"JetBrains Mono"', "ui-monospace", "monospace"],
        display: ['"Outfit"', "ui-sans-serif", "system-ui"],
      },
      boxShadow: {
        glow: "0 0 0 1px #F59E0B inset",
      },
      animation: {
        blink: "blink 1s steps(2) infinite",
        scan: "scan 4s linear infinite",
      },
      keyframes: {
        blink: { "50%": { opacity: 0 } },
        scan: {
          "0%": { transform: "translateY(-100%)" },
          "100%": { transform: "translateY(100%)" },
        },
      },
    },
  },
  plugins: [],
};
