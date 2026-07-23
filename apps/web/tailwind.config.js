/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{js,ts,jsx,tsx}"],
  theme: {
    extend: {
      colors: {
        relay: {
          ink: "#0f172a",
          slate: "#1e293b",
          mist: "#f1f5f9",
          line: "#e2e8f0",
          cyan: "#0891b2",
          "cyan-dark": "#0e7490",
          mint: "#14b8a6",
          danger: "#e11d48",
          warn: "#d97706",
        },
        surface: {
          page: "#f8fafc",
          card: "#ffffff",
          muted: "#f1f5f9",
          border: "#e2e8f0",
        },
        ink: {
          primary: "#0f172a",
          secondary: "#475569",
          muted: "#64748b",
        },
      },
      fontFamily: {
        sans: ["Outfit", "system-ui", "sans-serif"],
        display: ["Sora", "Outfit", "system-ui", "sans-serif"],
        mono: ["IBM Plex Mono", "ui-monospace", "monospace"],
      },
      boxShadow: {
        card: "0 1px 2px rgb(15 23 42 / 0.04), 0 8px 24px rgb(15 23 42 / 0.06)",
        soft: "0 12px 40px rgb(8 145 178 / 0.12)",
      },
      backgroundImage: {
        "relay-mesh":
          "radial-gradient(ellipse 70% 50% at 15% 10%, rgb(8 145 178 / 0.12), transparent 55%), radial-gradient(ellipse 50% 40% at 90% 0%, rgb(20 184 166 / 0.1), transparent 45%), linear-gradient(180deg, #f8fafc 0%, #eef6f8 100%)",
        "relay-sidebar": "linear-gradient(180deg, #0f172a 0%, #1e293b 100%)",
      },
    },
  },
  plugins: [],
};
