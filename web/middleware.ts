import createMiddleware from "next-intl/middleware";

export default createMiddleware({
  locales: ["ar", "en", "ur", "hi", "fil"],
  defaultLocale: "ar"
});

export const config = {
  matcher: ["/((?!api|_next|.*\\..*).*)"]
};
