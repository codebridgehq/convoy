## [1.0.0](https://github.com/codebridgehq/convoy/compare/v0.2.0...v1.0.0) (2026-03-09)


### ⚠ BREAKING CHANGES

* Existing BatchSchedulerWorkflow instances must be
terminated before deploying this change to avoid nondeterminism errors.

### ✨ Features

* implement simultaneous batch processing with child workflows ([36f467d](https://github.com/codebridgehq/convoy/commit/36f467d8a2b06da8037fa357fc1020520074b8ed))

## [0.2.0](https://github.com/codebridgehq/convoy/compare/v0.1.1...v0.2.0) (2026-03-08)


### ✨ Features

* add project-level authentication with api keys ([b26955d](https://github.com/codebridgehq/convoy/commit/b26955d447a73f616ffc425e4dff4c8647af6942))


### 📚 Documentation

* add pr and issue templates ([0f97c77](https://github.com/codebridgehq/convoy/commit/0f97c773c41fbd93027d92140024cfd3ca9d4405))
* fix repository url in quick start clone command ([b6a2f7e](https://github.com/codebridgehq/convoy/commit/b6a2f7e4c059a2ab067d93b7d78930d98d50c0da))
* reorganize documentation for open-source release ([0859f35](https://github.com/codebridgehq/convoy/commit/0859f3576b15ad65ffe4467805394167b8fce2f9))
* update documentation for projects, authentication, and docker hub images ([c335fd6](https://github.com/codebridgehq/convoy/commit/c335fd6ce8322fe4c931338cf5d559bb5b14a813))

## [0.1.1](https://github.com/codebridgehq/convoy/compare/v0.1.0...v0.1.1) (2026-03-08)


### 🐛 Bug Fixes

* add convoy-migrations service to run database migrations ([3f2e322](https://github.com/codebridgehq/convoy/commit/3f2e3229d8f314afec7d220f1eb891ea919bf781))
* **ci:** allow semantic-release commits by disabling body-max-line-length ([0d05562](https://github.com/codebridgehq/convoy/commit/0d05562128d9ed2faef7ed70cba6d3894f5e5448))


### 📚 Documentation

* **docker:** add docker-compose example for running convoy with docker hub images ([760cb4d](https://github.com/codebridgehq/convoy/commit/760cb4dab748443efae82cbf70ed12f2e380423a))
