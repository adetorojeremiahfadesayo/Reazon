import { defineConfig, type ViteDevServer } from "vite";
import react from "@vitejs/plugin-react";
import type { ChildProcess } from "node:child_process";
import { spawn } from "node:child_process";
import { existsSync } from "node:fs";
import { dirname, join, resolve } from "node:path";
import { fileURLToPath } from "node:url";

const webDir = dirname(fileURLToPath(import.meta.url));
const rootDir = resolve(webDir, "..");
const externalApiBaseUrl = cleanEnvValue(process.env.VITE_API_BASE_URL);
const requestedApiPort = Number(cleanEnvValue(process.env.VITE_API_PORT) ?? cleanEnvValue(process.env.API_PORT) ?? 8000);
const apiPort = Number.isInteger(requestedApiPort) && requestedApiPort > 0 ? requestedApiPort : 8000;
const apiTarget = externalApiBaseUrl ?? `http://127.0.0.1:${apiPort}`;

function cleanEnvValue(value: string | undefined) {
  const trimmed = value?.trim();
  return trimmed ? trimmed.replace(/\/+$/, "") : undefined;
}

function envFlagEnabled(value: string | undefined) {
  return ["1", "true", "yes", "on"].includes(value?.trim().toLowerCase() ?? "");
}

function localPythonPath() {
  const candidates = [
    join(rootDir, ".venv", "Scripts", "python.exe"),
    join(rootDir, ".venv", "bin", "python")
  ];
  return candidates.find((candidate) => existsSync(candidate)) ?? cleanEnvValue(process.env.PYTHON) ?? "python";
}

async function isApiHealthy(timeoutMs = 750) {
  const controller = new AbortController();
  const timeout = setTimeout(() => controller.abort(), timeoutMs);
  try {
    const response = await fetch(`${apiTarget}/health`, { signal: controller.signal });
    if (!response.ok) {
      return false;
    }
    const data = (await response.json().catch(() => undefined)) as { status?: string } | undefined;
    return data?.status === "healthy";
  } catch {
    return false;
  } finally {
    clearTimeout(timeout);
  }
}

async function waitForApi(timeoutMs = 45000) {
  const deadline = Date.now() + timeoutMs;
  while (Date.now() < deadline) {
    if (await isApiHealthy(1000)) {
      return true;
    }
    await new Promise((resolvePoll) => setTimeout(resolvePoll, 400));
  }
  return false;
}

function autoStartApi() {
  let apiProcess: ChildProcess | undefined;
  let apiStartup: Promise<boolean> | undefined;

  function startApi(server: ViteDevServer) {
    server.config.logger.info(`Starting Reazon API at ${apiTarget}`);
    apiProcess = spawn(
      localPythonPath(),
      ["-m", "uvicorn", "api.main:app", "--host", "127.0.0.1", "--port", String(apiPort)],
      {
        cwd: rootDir,
        env: { ...process.env, PYTHONUNBUFFERED: "1" },
        stdio: ["ignore", "pipe", "pipe"]
      }
    );

    apiProcess.stdout?.on("data", (chunk) => {
      server.config.logger.info(`[api] ${chunk.toString().trimEnd()}`);
    });
    apiProcess.stderr?.on("data", (chunk) => {
      server.config.logger.warn(`[api] ${chunk.toString().trimEnd()}`);
    });
    apiProcess.on("error", (error) => {
      server.config.logger.error(`Could not start Reazon API: ${error.message}`);
    });
    apiProcess.on("exit", (code, signal) => {
      apiProcess = undefined;
      if (code !== 0 && signal !== "SIGTERM") {
        server.config.logger.warn(`Reazon API stopped unexpectedly with code ${code ?? signal}`);
      }
    });
  }

  async function ensureApiReady(server: ViteDevServer) {
    if (await isApiHealthy()) {
      return true;
    }

    if (!apiStartup) {
      if (!apiProcess || apiProcess.killed || apiProcess.exitCode !== null) {
        startApi(server);
      } else {
        server.config.logger.info(`Waiting for Reazon API at ${apiTarget}`);
      }

      apiStartup = waitForApi().finally(() => {
        apiStartup = undefined;
      });
    }

    return apiStartup;
  }

  return {
    name: "reazon-auto-start-api",
    apply: "serve" as const,
    async configureServer(server) {
      if (envFlagEnabled(process.env.REAZON_DISABLE_AUTO_API) || externalApiBaseUrl) {
        return;
      }

      server.middlewares.use(async (req, res, next) => {
        const url = req.url ?? "";
        if (!url.startsWith("/api") && !url.startsWith("/health") && !url.startsWith("/reports")) {
          next();
          return;
        }

        const ready = await ensureApiReady(server);
        if (ready) {
          next();
          return;
        }

        res.statusCode = 503;
        res.setHeader("Content-Type", "application/json");
        res.end(
          JSON.stringify({
            detail: `Reazon API is not healthy at ${apiTarget}. Check the Vite terminal for API startup errors.`
          })
        );
      });

      if (await isApiHealthy()) {
        server.config.logger.info(`Reazon API is already running at ${apiTarget}`);
        return;
      }

      const stopApi = () => {
        if (apiProcess && !apiProcess.killed) {
          apiProcess.kill();
        }
      };
      process.once("SIGINT", stopApi);
      process.once("SIGTERM", stopApi);
      process.once("exit", stopApi);

      void ensureApiReady(server).then((ready) => {
        if (ready) {
          server.config.logger.info(`Reazon API is ready at ${apiTarget}`);
        } else {
          server.config.logger.warn(
            `Reazon API did not become healthy at ${apiTarget}. Check the API logs above.`
          );
        }
      });
    }
  };
}

export default defineConfig({
  plugins: [react(), autoStartApi()],
  preview: {
    allowedHosts: true
  },
  server: {
    port: 5173,
    proxy: {
      "/api": apiTarget,
      "/health": apiTarget,
      "/reports": apiTarget
    }
  }
});
