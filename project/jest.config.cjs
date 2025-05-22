module.exports = {
  preset: 'ts-jest',
  testEnvironment: 'jsdom',
  setupFilesAfterEnv: ['@testing-library/jest-dom'], // if you use jest-dom matchers
  moduleNameMapper: {
    // Handle module aliases (if any - adjust if your tsconfig has paths)
    '^@components/(.*)$': '<rootDir>/src/components/$1',
    '^@utils/(.*)$': '<rootDir>/src/utils/$1',
    // If you have CSS modules or other non-JS assets, you might need to mock them
    '\\.(css|less|scss|sass)$': 'identity-obj-proxy', 
  },
  transform: {
    '^.+\\.(ts|tsx)$': ['ts-jest', {
      tsconfig: 'tsconfig.json', // Ensure it points to your TS config
    }],
  },
  // Usually, you don't need to transform node_modules. 
  // However, if some package is distributed as ES module, you might need to add it to transformIgnorePatterns.
  // Example: '/node_modules/(?!(some-es-module-package|another-es-module-package)/)'
  transformIgnorePatterns: [
     "/node_modules/(?![@automerge/automerge-repo])" 
     // Add other ES module packages here if they cause issues, e.g.
     // "/node_modules/(?!(other-es-module-package|yet-another-es-module))"
  ],
  // Coverage reporting (optional)
  // collectCoverage: true,
  // coverageDirectory: "coverage",
  // coverageReporters: ["json", "lcov", "text", "clover"],
};
