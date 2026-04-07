import { defineConfig } from 'vitest/config'
import react from '@vitejs/plugin-react'
import path from 'path'
import { fileURLToPath } from 'url'

const __dirname = path.dirname(fileURLToPath(import.meta.url))
const FRONTEND_COVERAGE_SCOPE = process.env.FRONTEND_COVERAGE_SCOPE ?? 'phase0'
const FRONTEND_COVERAGE_BATCH_MODE = process.env.FRONTEND_COVERAGE_BATCH_MODE === '1'
const FRONTEND_COVERAGE_REPORTS_DIR =
  process.env.FRONTEND_COVERAGE_REPORTS_DIR ?? '../../.runtime-cache/test/coverage/apps/web'

const phase0CoverageInclude = [
  'src/app/**/*.{ts,tsx}',
  'src/components/**/*.{ts,tsx}',
  'src/lib/**/*.{ts,tsx}',
  'src/hooks/**/*.{ts,tsx}',
  'src/stores/**/*.{ts,tsx}',
]

const phase1CoverageExtraInclude = [
  'src/lib/api/client.ts',
  'src/lib/utils/error-handler.ts',
]

const coverageInclude =
  FRONTEND_COVERAGE_SCOPE === 'phase1'
    ? [...phase0CoverageInclude, ...phase1CoverageExtraInclude]
    : phase0CoverageInclude

const coverageExclude = [
  '**/*.d.ts',
  '**/*.test.{ts,tsx}',
  '**/*.spec.{ts,tsx}',
  'src/test/**',
  'src/**/__tests__/**',
  'src/lib/api/generated/**',
]

export default defineConfig({
  plugins: [react()],
  test: {
    environment: 'jsdom',
    fileParallelism: FRONTEND_COVERAGE_BATCH_MODE ? false : undefined,
    globals: true,
    setupFiles: ['./src/test/setup.ts'],
    exclude: ['e2e/**', 'e2e-live/**', 'node_modules/**', '.next/**', '.runtime-cache/build/next/**'],
    coverage: {
      provider: 'istanbul',
      clean: !FRONTEND_COVERAGE_BATCH_MODE,
      cleanOnRerun: !FRONTEND_COVERAGE_BATCH_MODE,
      reporter: FRONTEND_COVERAGE_BATCH_MODE ? ['json'] : ['text', 'html', 'lcov', 'json'],
      processingConcurrency: FRONTEND_COVERAGE_BATCH_MODE ? 1 : undefined,
      reportsDirectory: FRONTEND_COVERAGE_REPORTS_DIR,
      include: coverageInclude,
      exclude: coverageExclude,
      thresholds: {
        branches: 95,
        functions: 95,
        statements: 95,
        lines: 95,
      },
    },
    alias: {
      '@': path.resolve(__dirname, './src')
    }
  }
})
