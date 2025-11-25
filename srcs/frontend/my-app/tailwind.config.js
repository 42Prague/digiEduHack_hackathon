/** @type {import('tailwindcss').Config} */
module.exports = {
  darkMode: "class", // we’ll toggle `dark` class on <html> or <body>
  content: [
    "./index.html",
    "./src/**/*.{ts,tsx,js,jsx}",
  ],
  theme: {
    extend: {
      colors: {
        // central place to tweak brand colors
        primary: {
          DEFAULT: "#2563eb",
          dark: "#1d4ed8",
          light: "#60a5fa",
        },
        accent: {
          DEFAULT: "#10b981",
        },
      },
    },
  },
  plugins: [],
};
