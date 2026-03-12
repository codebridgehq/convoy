## [1.2.0](https://github.com/codebridgehq/convoy/compare/v1.1.1...v1.2.0) (2026-03-12)


### ✨ Features

* **worker:** add automatic batch failure recovery ([7f332bb](https://github.com/codebridgehq/convoy/commit/7f332bb98844ec292fb3318352ef759dfa8c45f0))


### 📚 Documentation

* fix test docker command to use convoy-tests ([d530537](https://github.com/codebridgehq/convoy/commit/d530537ca08ee75aa22bcf34b6eafee649c66182))

## [1.1.1](https://github.com/codebridgehq/convoy/compare/v1.1.0...v1.1.1) (2026-03-12)


### 🐛 Bug Fixes

* **bedrock:** use inference profiles for newer models ([344b446](https://github.com/codebridgehq/convoy/commit/344b446ef6b1150bdf2527fefe3d12292e207067))


### 📚 Documentation

* add contributor covenant code of conduct ([cc787ea](https://github.com/codebridgehq/convoy/commit/cc787ea20956beacfc4bd435067d24bd15b8c095))
* remove coming soon examples for aws fargate and digital ocean ([a7daf70](https://github.com/codebridgehq/convoy/commit/a7daf707059790d585f946de777d0cdc72c5a07f))
* update hosted api callout to reflect beta status with waitlist link ([6bc9467](https://github.com/codebridgehq/convoy/commit/6bc9467bfb429632e733ee26fa9249cd1b855d75))

## [1.1.0](https://github.com/codebridgehq/convoy/compare/v1.0.1...v1.1.0) (2026-03-10)


### ✨ Features

* group bedrock batch requests by model ([2b85da2](https://github.com/codebridgehq/convoy/commit/2b85da20e04e211afad2a2ea435e706830baef8b))
* implement provider-agnostic model ids ([cf8052b](https://github.com/codebridgehq/convoy/commit/cf8052bc33e306ee78437fda3752bd6f063f5e3d))


### 📚 Documentation

* add target blank to youtube video link in readme ([21db4e8](https://github.com/codebridgehq/convoy/commit/21db4e85a68a29704ee08d81ca31482ddd43910f))
* update readme to link youtube video instead of local file ([bd20cd3](https://github.com/codebridgehq/convoy/commit/bd20cd30fa9cdc63a2b861e13ddd798c8854206f))

## [1.0.1](https://github.com/codebridgehq/convoy/compare/v1.0.0...v1.0.1) (2026-03-09)


### 🐛 Bug Fixes

* add 405 to non-retryable http status codes in callback delivery ([6236f64](https://github.com/codebridgehq/convoy/commit/6236f6434c48c50be7f61abc6b2ef59d55cf8861))
* use system ssl certificates for https callback delivery ([a72c43d](https://github.com/codebridgehq/convoy/commit/a72c43d496a4038d6a69467b38573aa1480dd812))


### 📚 Documentation

* add explainer video link to readme ([33397e1](https://github.com/codebridgehq/convoy/commit/33397e1f38e12d1afbb746cc7e77073e66e9db08))

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
