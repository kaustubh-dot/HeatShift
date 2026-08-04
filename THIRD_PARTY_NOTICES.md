# HeatShift third-party notices

This file records the direct runtime, build, test, and bundled-font dependencies used by the candidate release. Versions are taken from `backend/requirements*.txt`, `frontend/package.json`, and the installed package metadata used for the release rehearsal. This is an attribution record, not legal advice.

## Backend and test dependencies

| Package | Pinned version | License | Attribution / license source |
|---|---:|---|---|
| OR-Tools | 9.15.6755 | Apache License 2.0 | [Google OR-Tools](https://github.com/google/or-tools); the package license is Apache 2.0. |
| Pydantic | 2.13.4 | MIT | [Pydantic](https://github.com/pydantic/pydantic) |
| FastAPI | 0.141.1 | MIT | [FastAPI](https://github.com/fastapi/fastapi) |
| Uvicorn | 0.52.0 | BSD 3-Clause | [Uvicorn](https://github.com/encode/uvicorn) |
| Pytest | 9.1.1 | MIT | [Pytest](https://github.com/pytest-dev/pytest) |
| HTTPX | 0.28.1 | BSD 3-Clause | [HTTPX](https://github.com/encode/httpx) |

OR-Tools brings transitive scientific/runtime packages such as NumPy, pandas, protobuf, and absl-py. They are installed from the pinned dependency graph and retain their own upstream notices; this repository does not copy their source or license files into the application bundle.

## Frontend and build dependencies

| Package | Pinned version | License | Attribution / license source |
|---|---:|---|---|
| React | 19.2.8 | MIT | [React](https://github.com/facebook/react) |
| React DOM | 19.2.8 | MIT | [React](https://github.com/facebook/react) |
| Vite | 8.1.5 | MIT | [Vite](https://github.com/vitejs/vite) |
| `@vitejs/plugin-react` | 6.0.2 | MIT | [Vite React plugin](https://github.com/vitejs/vite-plugin-react) |
| Lucide React | 1.17.0 | ISC | [Lucide](https://github.com/lucide-icons/lucide) |
| TypeScript | 5.9.3 | Apache-2.0 | [TypeScript](https://github.com/microsoft/TypeScript) |
| Vitest | 3.2.7 | MIT | [Vitest](https://github.com/vitest-dev/vitest) |
| React Testing Library | 16.3.0 | MIT | [Testing Library](https://github.com/testing-library/react-testing-library) |
| `@testing-library/jest-dom` | 6.8.0 | MIT | [jest-dom](https://github.com/testing-library/jest-dom) |
| jsdom | 26.1.0 | MIT | [jsdom](https://github.com/jsdom/jsdom) |

The repository commits `frontend/package-lock.json` but does not commit `frontend/node_modules`; `npm ci` must be used to reconstruct the locked graph. Transitive npm packages retain their package-provided license metadata.

## Bundled fonts

The following font files are served locally from `frontend/public/fonts/` and have their complete license text committed beside them:

| Font family | Bundled files | License and attribution |
|---|---|---|
| DM Sans | `dm-sans-variable.woff2` | SIL Open Font License 1.1; The DM Sans Project Authors. See `DM-Sans-OFL.txt`. |
| JetBrains Mono | `jetbrains-mono-variable.woff2` | SIL Open Font License 1.1; The JetBrains Mono Project Authors. See `JetBrains-Mono-OFL.txt`. |
| Space Grotesk | `space-grotesk-700.woff2` | SIL Open Font License 1.1; The Space Grotesk Project Authors. See `Space-Grotesk-OFL.txt`. |

No runtime CDN, external font URL, map tile, analytics, remote image, or external data service is required by the release build.

## Project scope

HeatShift's own source and synthetic fixtures do not add a separate third-party library license beyond the dependencies listed above. The bundled policy and scenario are synthetic project data, not an endorsement or certification by any package author or font author.
