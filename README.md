# Project README

## EthiViz Dashboard

An advanced Ethics Analysis Dashboard that evaluates bias and ethical dimensions in text and image content across multiple cultural frameworks. Built with **React**, **TypeScript**, and modern web technologies.

---

## 🚀 Tech Stack

- **Frontend Framework:** React 18+ with TypeScript
- **Programming Language:** Python
- **Build Tool:** Vite for fast development and optimized builds  
- **Styling:** Tailwind CSS with PostCSS processing  
- **Code Quality:** ESLint with TypeScript and React-specific rules  
- **Icons:** Lucide React (optimized for performance)  

---

## 🏗 Application Architecture

### Core Components

- **App.tsx** – Main application container with state management  
  - Global state for analysis results, job tracking, and UI state  
  - API polling logic for asynchronous job processing  
  - E2E testing mode with mock data injection  
  - Error handling and loading states  
- **ConfigPanel** – Configuration sidebar for analysis setup  
- **MainContent** – Main dashboard area for displaying results  

### Key Features Implementation

**Multi-Framework Ethics Analysis**  
The application analyzes content across four ethical frameworks:

- Western Ethics: Traditional Western philosophical approaches  
- Ubuntu Ethics: African philosophical framework emphasizing interconnectedness  
- Confucian Ethics: East Asian virtue-based ethical system  
- Islamic Ethics: Islamic moral and ethical principles  

**Asynchronous Processing System**

**Analysis Data Structure**

**E2E Testing Infrastructure**  
Built-in testing mode with configurable mock data:

- Comprehensive test data  
- Text-only scenarios  
- Image-only scenarios  
- Missing fields testing  
- Empty state testing  

---

## 📁 Project Structure

```typescript
// Polling mechanism for job status
const POLLING_INTERVAL = 3000;  // 3 seconds
const MAX_POLLING_ATTEMPTS = 20;  // 1 minute timeout

interface AnalysisResults {
  text_analysis: TextAnalysis[];
  image_analysis: Record<string, ImageAnalysis>;
}
```

```
├── src/
│   ├── components/
│   │   ├── ConfigPanel.tsx    # Analysis configuration sidebar
│   │   └── MainContent.tsx    # Results dashboard
│   ├── utils/
│   │   └── types.ts           # TypeScript type definitions
│   ├── App.tsx                # Main application component
│   ├── main.tsx               # Application entry point
│   ├── index.css              # Tailwind CSS imports
│   └── vite-env.d.ts          # Vite environment types
├── dist/                      # Build output (ignored by ESLint)
├── index.html                 # Main HTML template
├── vite.config.ts             # Vite configuration
├── tailwind.config.js         # Tailwind CSS configuration
├── postcss.config.js          # PostCSS configuration
├── eslint.config.js           # ESLint configuration
├── tsconfig.json              # TypeScript project references
├── tsconfig.app.json          # App-specific TypeScript config
└── tsconfig.node.json         # Node.js/build tools TypeScript config
```

---

## 🛠 Development Setup

### Requirements

- Node.js (version 18+ recommended)  
- npm, yarn, or pnpm  

### Installation

```bash
# Clone the repository
git clone <repository-url>
cd <project-directory>

# Install dependencies
npm install
# or
yarn install
# or
pnpm install
```

### Development Commands

```bash
# Start development server
npm run dev

# Build for production
npm run build

# Preview production build
npm run preview

# Run linter
npm run lint

# Fix linting issues
npm run lint:fix
```

---

## ⚙ Configuration Details

### TypeScript Configuration

The project uses a composite TypeScript setup with separate configurations:

- **tsconfig.json** – Root configuration with project references  
- **tsconfig.app.json** – Application code configuration (ES2020, React JSX)  
- **tsconfig.node.json** – Build tools configuration (ES2022, for Vite config)  

**Key TypeScript Features Enabled:**

- Strict type checking  
- Unused variable/parameter detection  
- No fallthrough cases in switch statements  
- React JSX transformation  
- Bundler module resolution  

### ESLint Configuration

- **Base:** JavaScript and TypeScript recommended rules  
- **React Hooks:** Enforces Rules of Hooks  
- **React Refresh:** Ensures components are properly exportable for HMR  
- **Scope:** All `.ts` and `.tsx` files  
- **Environment:** Browser globals (ES2020)  

### Vite Configuration

Optimized for React development:

- React Plugin: Enables JSX transformation and Fast Refresh  
- Dependency Optimization: Excludes `lucide-react` from pre-bundling for better performance  
- Development: Fast HMR and instant server start  
- Production: Tree-shaking and code splitting  

### Tailwind CSS

Configured to:

- **Scan:** All HTML, JS, TS, JSX, and TSX files in `src/`  
- **Process:** Through PostCSS with Autoprefixer  
- **Extend:** Theme customization ready  
- **Optimize:** Unused styles purged in production  

---

## 🔧 Build Process

1. Development: Vite serves files with HMR and instant compilation  
2. Linting: ESLint checks code quality and React patterns  
3. Styling: Tailwind generates utility classes, PostCSS adds vendor prefixes  
4. Type Checking: TypeScript ensures type safety  
5. Production: Vite bundles and optimizes for deployment  

---

## 📦 Dependencies

### Dependencies

- `react` – UI library  
- `react-dom` – DOM rendering  
- `axios` – HTTP client for API communication  
- `lucide-react` – Icon library (performance optimized)  

### Development Dependencies

- `@vitejs/plugin-react` – Vite React plugin  
- `typescript` – Type checking  
- `@typescript-eslint/parser` & `@typescript-eslint/eslint-plugin` – TypeScript linting  
- `eslint-plugin-react-hooks` – React Hooks linting  
- `eslint-plugin-react-refresh` – HMR compatibility  
- `tailwindcss` – CSS framework  
- `autoprefixer` – CSS vendor prefixes  

---

## 🚀 API Integration

The application connects to a backend API server:

### Workflow

1. **Job Submission:** Analysis requests are submitted to the API  
2. **Polling:** Status is checked every 3 seconds via the status URL  
3. **Results Retrieval:** Completed analyses are fetched and displayed  
4. **Error Handling:** Failed jobs and timeouts are gracefully handled  

---

## 🎯 Key Features

- Multi-Cultural Ethics Analysis: Western, Ubuntu, Confucian, Islamic frameworks  
- Dual Content Analysis: Supports text and image analysis  
- Bias Detection: Advanced bias scoring and diversity index calculations  
- Real-time Processing: Asynchronous job processing with status polling  
- Visual Dashboard: Interactive UI with comprehensive analysis results  
- E2E Testing Mode: Built-in testing with mock data  
- Responsive Design: Accessible interface with smooth animations  

---

## 🚦 Getting Started

### Backend Setup

Ensure the backend API server is running at:  

```
http://localhost:5001
```

### Frontend Setup

1. Install dependencies and start the development server  
2. Toggle E2E mode using the banner toggle  
3. Configure analysis in the sidebar panel  
4. Submit content for ethics analysis  
5. View results in the main dashboard area  

---

## 🔍 Analysis Capabilities

### Text Analysis

- Bias Detection: Quantifies potential bias  
- Diversity Assessment: Measures inclusivity  
- Multi-Cultural Ethics: Evaluates across four frameworks  

### Image Analysis

- Visual Bias Detection: Identifies representation bias  
- Demographic Analysis: Skin tone and gender representation  
- Object Recognition: Categorization of visual elements  
- Cultural Ethics Assessment: Framework-based evaluation  

**Supported Metrics**

- Bias Score (0-1 scale)  
- Diversity Index (0-1 scale)  
- Ethics Scores (0-10 scale)  
- Demographic distributions  
- Object/face counts  

---

## 📝 Development Guidelines

- Write TypeScript with strict type checking  
- Use functional components with hooks  
- Follow React Hooks rules (enforced by ESLint)  
- Utilize Tailwind utilities for styling  
- Keep components exportable for HMR  
- Run linting before commits  

```typescript
const currentTestData: AnalysisResults = missingFieldsData;  // Switch here
```

---

This setup provides a solid foundation for building modern, scalable React applications with excellent developer experience and production-ready optimizations.
