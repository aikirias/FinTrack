/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    "./src/app/**/*.{js,ts,jsx,tsx}",
    "./src/components/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        primary: "#0f172a",
        secondary: "#0b1324",
        accent: "#0ea5e9",
        accentSoft: "#38bdf8",
      },
    },
  },
  plugins: [],
};
