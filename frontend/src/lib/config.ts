export const config = {
  demo:
    import.meta.env.VITE_DEMO_MODE === "true" &&
    ["localhost", "127.0.0.1", "[::1]"].includes(window.location.hostname),
  api: import.meta.env.VITE_API_URL || "/api",
  region: import.meta.env.VITE_REGION || "us-east-2",
  userPoolId: import.meta.env.VITE_USER_POOL_ID || "",
  userPoolClientId: import.meta.env.VITE_USER_POOL_CLIENT_ID || "",
};
