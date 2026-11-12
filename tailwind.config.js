/** @type {import('tailwindcss').Config} */
module.exports = {
  content: ["./templates/**/*.html", "./app.py"],
  theme: {
    extend: {
      fontFamily: {
        sans: ["Geist", "-apple-system", "BlinkMacSystemFont", "sans-serif"],
        serif: ["Newsreader", "Georgia", "serif"],
        mono: ["Geist Mono", "SF Mono", "monospace"],
      },
      colors: {
        canvas: "#FBFBFA",
        surface: "#FFFFFF",
        borderSubtle: "#EAEAEA",
        ink: "#111111",
        muted: "#6E6D6A",
      },
    },
  },
  plugins: [],
};
