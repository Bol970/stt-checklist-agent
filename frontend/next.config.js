/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  // Сборку не валим из-за отсутствия ESLint-конфига (его в проекте нет).
  eslint: { ignoreDuringBuilds: true },
};

module.exports = nextConfig;
