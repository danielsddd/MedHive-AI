/**
 * Next.js config. Biome is the single TS linter, so the default Next ESLint integration is
 * disabled during builds (gotcha #8 — avoids fix-on-save conflicts). reactStrictMode on.
 * No business API routes live in Next.js — it is auth/session glue only (hard rule).
 */
/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  eslint: { ignoreDuringBuilds: true },
  output: 'standalone', // self-contained server bundle for the production Docker image
}
module.exports = nextConfig
