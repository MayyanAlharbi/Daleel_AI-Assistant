import createNextIntlPlugin from "next-intl/plugin";

const withNextIntl = createNextIntlPlugin("./i18n/request.ts");

const nextConfig = {
  // keep your existing config here if you have one
};

export default withNextIntl(nextConfig);
