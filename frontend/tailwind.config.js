/** @type {import('tailwindcss').Config} */
module.exports = {
  content: ["./app/**/*.{js,ts,jsx,tsx}", "./components/**/*.{js,ts,jsx,tsx}"],
  theme: {
    extend: {
      colors: {
        ink:    "#0D0D0D",
        paper:  "#F5F2ED",
        cream:  "#EDE8E1",
        amber:  "#D97706",
        "amber-light": "#FEF3C7",
        sage:   "#4A5E52",
        mist:   "#8B9E93",
        border: "#DDD8D0",
        danger: "#EF4444",
      },
      fontFamily: {
        display: ["var(--font-display)", "serif"],
        mono:    ["var(--font-mono)",    "monospace"],
        body:    ["var(--font-body)",    "sans-serif"],
      },
      animation: {
        "fade-up":   "fadeUp 0.35s ease forwards",
        "fade-in":   "fadeIn 0.25s ease forwards",
        "slide-in":  "slideIn 0.3s cubic-bezier(0.16,1,0.3,1) forwards",
        "spin-slow": "spin 2s linear infinite",
      },
      keyframes: {
        fadeUp:  { "0%": { opacity:"0", transform:"translateY(10px)" }, "100%": { opacity:"1", transform:"translateY(0)" } },
        fadeIn:  { "0%": { opacity:"0" }, "100%": { opacity:"1" } },
        slideIn: { "0%": { opacity:"0", transform:"translateX(-10px)" }, "100%": { opacity:"1", transform:"translateX(0)" } },
      },
    },
  },
  plugins: [],
};
