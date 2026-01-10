# Changelog

## [3.0.0](https://github.com/grandcamel/JIRA-Assistant-Skills/compare/v2.2.7...v3.0.0) (2026-01-10)


### ⚠ BREAKING CHANGES

* Major version bump to 3.0.0
* Major version bump to 3.0.0

### Features

* bump to v3.0.0 and add automated PyPI publishing ([adf99fb](https://github.com/grandcamel/JIRA-Assistant-Skills/commit/adf99fba64e40ab7d95cb8dc23e90b26fa214a3b))
* bump to v3.0.0 and add automated PyPI publishing ([8b89497](https://github.com/grandcamel/JIRA-Assistant-Skills/commit/8b89497f52c03ad661492762cb7c72d2d2586fc8))
* **jira-agile:** add sprint discovery commands ([791e2b2](https://github.com/grandcamel/JIRA-Assistant-Skills/commit/791e2b2e4fba622883169fa521adbbcded331a1c))
* **jira-agile:** add sprint discovery commands ([b7f0efa](https://github.com/grandcamel/JIRA-Assistant-Skills/commit/b7f0efae46b9d2f7022d431a342a2780944d6dd6))
* **jira-agile:** add velocity command and fix get_estimates bug ([54716e1](https://github.com/grandcamel/JIRA-Assistant-Skills/commit/54716e1fca26d0812f37ab277fc4fcdd1c21622b))
* **jira-agile:** add velocity command for sprint metrics ([e483b4b](https://github.com/grandcamel/JIRA-Assistant-Skills/commit/e483b4b2f25a5124cd24bd384ca35fbb8888ad11))
* **jira-bulk,jira-admin:** add bulk delete and permission diagnostics ([353598a](https://github.com/grandcamel/JIRA-Assistant-Skills/commit/353598a7e7ab83d8fae3c88395bd6dc9ebeff124))


### Bug Fixes

* **jira-agile:** add --top, --bottom, --board options to rank command ([e348047](https://github.com/grandcamel/JIRA-Assistant-Skills/commit/e348047d23b0c7b1a0c1fa6b4d7e17a83ebadc10))
* **jira-agile:** add --top, --bottom, --board options to rank command ([42c9c06](https://github.com/grandcamel/JIRA-Assistant-Skills/commit/42c9c06975b976b21e7f3a7a3fca4b51a8041736))
* **jira-agile:** use correct get_board_sprints method in get_estimates ([4f96df0](https://github.com/grandcamel/JIRA-Assistant-Skills/commit/4f96df0d4134ca4c3a92116ee6a55bc16c49fcd0))

## [2.2.7](https://github.com/grandcamel/JIRA-Assistant-Skills/compare/v2.2.6...v2.2.7) (2026-01-05)


### Bug Fixes

* **jira-admin:** fix user search positional query, screen field args, group user commands ([9c0480f](https://github.com/grandcamel/JIRA-Assistant-Skills/commit/9c0480f))
* **jira-agile:** align CLI wrapper with script interfaces for epic/sprint commands ([80869c2](https://github.com/grandcamel/JIRA-Assistant-Skills/commit/80869c2))
* **jira-assistant:** update hub skill documentation ([911a444](https://github.com/grandcamel/JIRA-Assistant-Skills/commit/911a444))
* **jira-bulk:** align CLI wrapper with script interfaces ([f611f1c](https://github.com/grandcamel/JIRA-Assistant-Skills/commit/f611f1c))
* **jira-collaborate:** add --max-results, --internal, --expand, --thumbnail, --no-notify options ([4cbdda7](https://github.com/grandcamel/JIRA-Assistant-Skills/commit/4cbdda7))
* **jira-dev:** align CLI wrapper with script interfaces for branch/PR commands ([4efa771](https://github.com/grandcamel/JIRA-Assistant-Skills/commit/4efa771))
* **jira-fields:** align CLI wrapper with script interfaces ([d73de54](https://github.com/grandcamel/JIRA-Assistant-Skills/commit/d73de54))
* **jira-issue:** improve SKILL.md documentation accuracy ([7d718fe](https://github.com/grandcamel/JIRA-Assistant-Skills/commit/7d718fe))
* **jira-jsm:** fix request comment syntax, add --internal-only, --show-jql, --dry-run options ([b145c28](https://github.com/grandcamel/JIRA-Assistant-Skills/commit/b145c28))
* **jira-lifecycle:** fix component --id usage, version --name option, transition options ([9583208](https://github.com/grandcamel/JIRA-Assistant-Skills/commit/9583208))
* **jira-ops:** fix cache command args (--category vs --type), remove invalid options ([0a43efa](https://github.com/grandcamel/JIRA-Assistant-Skills/commit/0a43efa))
* **jira-relationships:** align CLI wrapper with script interfaces ([1a7e5fe](https://github.com/grandcamel/JIRA-Assistant-Skills/commit/1a7e5fe))
* **jira-search:** align CLI wrapper with script interfaces ([3d2f01e](https://github.com/grandcamel/JIRA-Assistant-Skills/commit/3d2f01e))
* **jira-time:** align CLI wrapper with script interfaces ([b90e076](https://github.com/grandcamel/JIRA-Assistant-Skills/commit/b90e076))


### Documentation

* add parallel subagent pattern to CLAUDE.md ([924a5c0](https://github.com/grandcamel/JIRA-Assistant-Skills/commit/924a5c0))

## [2.1.0](https://github.com/grandcamel/JIRA-Assistant-Skills/compare/v2.0.1...v2.1.0) (2025-12-31)


### Features

* **ci:** add Docker image publishing to ghcr.io ([dd6ae87](https://github.com/grandcamel/JIRA-Assistant-Skills/commit/dd6ae87e685a6c5cd39cc12ddd2bcbd9d09b8b6c))


### Bug Fixes

* **ci:** lowercase Docker image name for ghcr.io ([425edbc](https://github.com/grandcamel/JIRA-Assistant-Skills/commit/425edbc87e061d8a583b2e67012145305864ee94))
* **cli:** prevent Exit exception from being caught as error ([7269a13](https://github.com/grandcamel/JIRA-Assistant-Skills/commit/7269a13b5a339a6d0509772d4073af0d222af715))
* **jira-search:** handle cursor-based pagination in search results ([8e828ce](https://github.com/grandcamel/JIRA-Assistant-Skills/commit/8e828ce4bfed5ed78fbbf6764dab1a193971bbb3))

## [2.0.1](https://github.com/grandcamel/JIRA-Assistant-Skills/compare/v2.0.0...v2.0.1) (2025-12-31)


### Bug Fixes

* **skills:** add enterprise fields to SKILL.md frontmatter ([b358635](https://github.com/grandcamel/JIRA-Assistant-Skills/commit/b3586352dd95e0b1786572ae1f4ba8749841ec2f))

## [1.1.0](https://github.com/grandcamel/jira-assistant-skills/compare/v1.0.3...v1.1.0) (2025-12-29)


### Features

* add jira-skills-marketplace plugin ([07caa1e](https://github.com/grandcamel/jira-assistant-skills/commit/07caa1eae9b4d646e58f0653351bda3e3d74af1d))

## [1.0.3](https://github.com/grandcamel/jira-assistant-skills/compare/v1.0.2...v1.0.3) (2025-12-28)


### Bug Fixes

* **ci:** skip broken test_get_blockers.py tests temporarily ([31c1959](https://github.com/grandcamel/jira-assistant-skills/commit/31c195914c098108473b1b7b53c14e8706120487))

## [1.0.2](https://github.com/grandcamel/jira-assistant-skills/compare/v1.0.1...v1.0.2) (2025-12-28)


### Bug Fixes

* **ci:** run tests per skill to avoid conftest conflicts ([9db4235](https://github.com/grandcamel/jira-assistant-skills/commit/9db4235cf5df226cbaa7d306a723a84b25a878d0))

## [1.0.1](https://github.com/grandcamel/jira-assistant-skills/compare/v1.0.0...v1.0.1) (2025-12-28)


### Bug Fixes

* **ci:** resolve pytest import path conflicts in release workflow ([edfae9c](https://github.com/grandcamel/jira-assistant-skills/commit/edfae9c3a5e73780f50fea7c7934dbfb1b013f80))

## 1.0.0 (2025-12-28)


### Features

* **ci:** add automated GitHub releases with conventional commits ([813032c](https://github.com/grandcamel/jira-assistant-skills/commit/813032cef0e54491316390e69b4bba0c094880cf))
* **ci:** add automated GitHub releases with conventional commits ([6c42ccc](https://github.com/grandcamel/jira-assistant-skills/commit/6c42ccc47a0003d290df8acea84c9cd634451dd3))
* **config:** add Agile field configuration with automatic discovery ([273357f](https://github.com/grandcamel/jira-assistant-skills/commit/273357f29ec5d1d627b5942f767f01bfaa3e0354))
* **devcontainer:** add GitHub Codespaces configuration ([781cd57](https://github.com/grandcamel/jira-assistant-skills/commit/781cd5738d58bcc4e78a66ab440a496e774f634e))
* **jira-admin:** add comprehensive admin scripts for JIRA administration ([bbc557f](https://github.com/grandcamel/jira-assistant-skills/commit/bbc557f2e9cb29484cb1e083a78d4ec2c13ac67b))
* **jira-admin:** add skill foundation with initial scripts and tests ([4752fe4](https://github.com/grandcamel/jira-assistant-skills/commit/4752fe4ea6e35c9c9b02402f39df47e70a6dd2d3))
* **jira-agile:** implement add_to_epic.py (7/7 tests passing) ([152a7b4](https://github.com/grandcamel/jira-assistant-skills/commit/152a7b42ad151b964f3dbcafac31c4d8e085fe6f))
* **jira-agile:** implement create_epic.py (7/7 tests passing) ([d0bc3f9](https://github.com/grandcamel/jira-assistant-skills/commit/d0bc3f912e19acfab75464ff122ccb01c421eda2))
* **jira-agile:** implement create_sprint.py (6/6 tests passing) ([cd972ce](https://github.com/grandcamel/jira-assistant-skills/commit/cd972ceb15ab6f68cf2bfc4bfa94b5e682a2f089))
* **jira-agile:** implement create_subtask.py (7/7 tests passing) ([e0c37d1](https://github.com/grandcamel/jira-assistant-skills/commit/e0c37d12e2bd162dcd887c99ea05e84321111710))
* **jira-agile:** implement estimate_issue.py (8/8 tests passing) ([82e07f1](https://github.com/grandcamel/jira-assistant-skills/commit/82e07f1833359a733c220a866159c19bf10d0ffe))
* **jira-agile:** implement get_backlog.py (5/5 tests passing) ([e9b068e](https://github.com/grandcamel/jira-assistant-skills/commit/e9b068e117c7e0b267a084bb989ab04fbd37d42a))
* **jira-agile:** implement get_epic.py (7/7 tests passing) ([8d36190](https://github.com/grandcamel/jira-assistant-skills/commit/8d36190f4c4c6bdb7ab955d9bf4d63b43a3c6bce))
* **jira-agile:** implement get_estimates.py (6/6 tests passing) ([6957fb9](https://github.com/grandcamel/jira-assistant-skills/commit/6957fb9ad27d6949918d21715ce65b9e8d366531))
* **jira-agile:** implement get_sprint.py (6/6 tests passing) ([702010c](https://github.com/grandcamel/jira-assistant-skills/commit/702010c5f56b953683c04cb345c5a52896253d16))
* **jira-agile:** implement manage_sprint.py (6/6 tests passing) ([d2c1706](https://github.com/grandcamel/jira-assistant-skills/commit/d2c1706413d1bc6ea9b1159e090a554101715e75))
* **jira-agile:** implement move_to_sprint.py (6/6 tests passing) ([4acc183](https://github.com/grandcamel/jira-assistant-skills/commit/4acc1830ca073bfa6643b6f4d57159981e699d72))
* **jira-agile:** implement rank_issue.py (6/6 tests passing) ([90706da](https://github.com/grandcamel/jira-assistant-skills/commit/90706daea98e4cfc5bb15e1bdb954c1e8857dfc8))
* **jira-agile:** migrate to configurable Agile field IDs ([adcbb57](https://github.com/grandcamel/jira-assistant-skills/commit/adcbb57e968b5dbbd10bf6754f2907cbcf64126e))
* **jira-assistant:** add meta-skill router with best practices guide ([77e9abb](https://github.com/grandcamel/jira-assistant-skills/commit/77e9abbbe9633a8e5e4fd5f5aee72ab5b3013f29))
* **jira-bulk,jira-dev,jira-ops,shared:** add new skills and infrastructure ([0c6cf48](https://github.com/grandcamel/jira-assistant-skills/commit/0c6cf48c4d9713714adaa9088d55d15752ab4af4))
* **jira-bulk:** add batching with checkpoint/resume for large operations ([30bf3bc](https://github.com/grandcamel/jira-assistant-skills/commit/30bf3bcc7bf5949f878b66285b1d0041c2d6b957))
* **jira-collaborate,jira-issue,jira-jsm,jira-ops,jira-relationships,jira-time:** enhance multiple skills ([f507f73](https://github.com/grandcamel/jira-assistant-skills/commit/f507f73daf77cd3a5ae882d95063e71ebbed62d1))
* **jira-collaborate:** add visibility support to add_comment.py (6/6 tests passing) ([da2bc8f](https://github.com/grandcamel/jira-assistant-skills/commit/da2bc8fa8502f088356765a23a61af49ae279bb0))
* **jira-collaborate:** implement delete_comment.py (5/5 tests passing) ([c06c7ab](https://github.com/grandcamel/jira-assistant-skills/commit/c06c7ab815e412b07eaa0ddd03de024c02d81a4b))
* **jira-collaborate:** implement get_activity.py (8/8 tests passing) ([ec5bc91](https://github.com/grandcamel/jira-assistant-skills/commit/ec5bc91de7debcefd3c2d90b7f4f15162d875bb7))
* **jira-collaborate:** implement get_comments.py (7/7 tests passing) ([2674759](https://github.com/grandcamel/jira-assistant-skills/commit/2674759b35476bb45f2e687b212c5b2585922a1a))
* **jira-collaborate:** implement send_notification.py (7/7 tests passing) ([43737da](https://github.com/grandcamel/jira-assistant-skills/commit/43737da5e910bead103c3ca6f920eecf943e9835))
* **jira-collaborate:** implement update_comment.py (5/5 tests passing) ([d70ffdd](https://github.com/grandcamel/jira-assistant-skills/commit/d70ffdd4dce636b83dfb6c86b7ce51daa997b611))
* **jira-fields:** add custom field management skill ([5fec73c](https://github.com/grandcamel/jira-assistant-skills/commit/5fec73c3e6d08d226bc7c4ea51e017a59a26e4a8))
* **jira-issue,jira-search,shared:** integrate time tracking across skills ([4692b6b](https://github.com/grandcamel/jira-assistant-skills/commit/4692b6b70eb9502d678225702e51286c306742ad))
* **jira-issue,jira-search:** integrate Agile fields ([8a4b248](https://github.com/grandcamel/jira-assistant-skills/commit/8a4b248fc0d09b4f6260035e4f649c1532a2d609))
* **jira-issue,jira-search:** integrate issue links across skills ([f7e9de4](https://github.com/grandcamel/jira-assistant-skills/commit/f7e9de4e4c53757307062fa8bb42a198096fca6a))
* **jira-jsm,shared:** add JSM API methods and live integration tests ([d30c391](https://github.com/grandcamel/jira-assistant-skills/commit/d30c39193274d6fa4217e2d6d7d2b3581a6f74bf))
* **jira-jsm:** complete Jira Service Management implementation ([2d81ecd](https://github.com/grandcamel/jira-assistant-skills/commit/2d81ecd480e5c724bbce2c6cc23d48905a0dfef1))
* **jira-lifecycle:** add sprint integration to transition_issue.py ([d5b19da](https://github.com/grandcamel/jira-assistant-skills/commit/d5b19da2d62c71eef3c0b971a1043ac4acc20715))
* **jira-lifecycle:** implement archive_version.py (4/4 tests passing) ([a9bbeae](https://github.com/grandcamel/jira-assistant-skills/commit/a9bbeaeeff757f38882cbbbcd8456cab69d38ae1))
* **jira-lifecycle:** implement create_component.py (6/6 tests passing) ([01d845d](https://github.com/grandcamel/jira-assistant-skills/commit/01d845d856fcc5065f67f6695da4f63955e676a3))
* **jira-lifecycle:** implement create_version.py (6/6 tests passing) ([904e7bd](https://github.com/grandcamel/jira-assistant-skills/commit/904e7bd32bea6b545adf44a32cd99fb0e99911fb))
* **jira-lifecycle:** implement delete_component.py (6/6 tests passing) ([a07e831](https://github.com/grandcamel/jira-assistant-skills/commit/a07e83135ad332006602cd5a8537f5f4729ede26))
* **jira-lifecycle:** implement get_components.py (6/6 tests passing) ([eb665cc](https://github.com/grandcamel/jira-assistant-skills/commit/eb665cc2b0c0ea0813515667e6c8ca15dd16a125))
* **jira-lifecycle:** implement get_versions.py (8/8 tests passing) ([272f4e3](https://github.com/grandcamel/jira-assistant-skills/commit/272f4e3ae3547b98c9044e4e30abf069d0997cd3))
* **jira-lifecycle:** implement move_issues_version.py (6/6 tests passing) ([ec02afd](https://github.com/grandcamel/jira-assistant-skills/commit/ec02afda4eee95502fede1207b89b04a1288b071))
* **jira-lifecycle:** implement release_version.py (6/6 tests passing) ([f62336f](https://github.com/grandcamel/jira-assistant-skills/commit/f62336f6919e03b48884a37678ec4c83c04f0144))
* **jira-lifecycle:** implement update_component.py (6/6 tests passing) ([38ae843](https://github.com/grandcamel/jira-assistant-skills/commit/38ae8434ace5e9b3dd2cfba72baff1f3fa6f1244))
* **jira-ops:** add project context discovery system ([38b4499](https://github.com/grandcamel/jira-assistant-skills/commit/38b4499be2a845501f775fc00edb9d3ef53eea57))
* **jira-relationships:** complete Phase 1 - Link Type Discovery ([6cf3ee9](https://github.com/grandcamel/jira-assistant-skills/commit/6cf3ee99bbad52469889d7ff2bbb90292582fd17))
* **jira-relationships:** complete Phase 2 - Basic Linking Operations ([2a7a3a4](https://github.com/grandcamel/jira-assistant-skills/commit/2a7a3a45c1b70ba2b063fdea90483938b6362a21))
* **jira-relationships:** complete Phase 3 - Dependency Analysis ([7275c6e](https://github.com/grandcamel/jira-assistant-skills/commit/7275c6ea43f306548d9a2a8cb39384b3fdea4fa2))
* **jira-relationships:** complete Phase 4 - Bulk Operations ([b149002](https://github.com/grandcamel/jira-assistant-skills/commit/b1490029c882c1a23eee039517f9d2805c4c8ab1))
* **jira-search:** add reporter field to default search results ([b9cbb10](https://github.com/grandcamel/jira-assistant-skills/commit/b9cbb105a8a8945f20932b41245172d67bd93a41))
* **jira-search:** enhance JQL tooling with history, interactive mode, and streaming ([2f94209](https://github.com/grandcamel/jira-assistant-skills/commit/2f942094dae2ce60c2d48044ada1ad0c6d6fe8f9))
* **jira-search:** implement Advanced Search & Reporting (JQL builder, filter CRUD, sharing) ([7cc0a99](https://github.com/grandcamel/jira-assistant-skills/commit/7cc0a99dac4dd2b12a5fc6142b272dab2a3ef6eb))
* **jira-time:** create skill structure and add time tracking infrastructure ([fa42fdc](https://github.com/grandcamel/jira-assistant-skills/commit/fa42fdcf5b63cafd9bebfffb1ca166bd0e665d6d))
* **jira-time:** implement Phase 1 - Worklog CRUD (32 tests) ([ca9fede](https://github.com/grandcamel/jira-assistant-skills/commit/ca9fede25c8d80d4053092bf853cd81f7c13481d))
* **jira-time:** implement Phases 2-4 (31 additional tests) ([2a4212b](https://github.com/grandcamel/jira-assistant-skills/commit/2a4212be5be77ef4db5bb245bcf2618d15557de3))
* **proposals:** add production-ready implementations for all proposals ([6a1028e](https://github.com/grandcamel/jira-assistant-skills/commit/6a1028e7aaf5b849786888a4a11486aef5793d94))
* **shared,jira-issue:** add "self" assignee support for auto-assignment ([4b381d0](https://github.com/grandcamel/jira-assistant-skills/commit/4b381d087f900f1aea56c0a5150f7c8cd188bb03))
* **shared:** add admin API methods to JiraClient ([78e075c](https://github.com/grandcamel/jira-assistant-skills/commit/78e075c66015ec270c6438ca675fb725d0b9a45c))
* **shared:** add automation API error classes ([4029b94](https://github.com/grandcamel/jira-assistant-skills/commit/4029b94c48e10442cea20dfe4916f0c1b4b8e83c))
* **shared:** add automation REST API client ([d57b463](https://github.com/grandcamel/jira-assistant-skills/commit/d57b4638d06e9844648a46f12721768025f19ad3))
* **shared:** add cross-platform easy setup system with keychain support ([f24f82b](https://github.com/grandcamel/jira-assistant-skills/commit/f24f82bded2ab7441d94d037a36de9688eca2466))
* **shared:** add helper modules for batch processing and user operations ([e6b8686](https://github.com/grandcamel/jira-assistant-skills/commit/e6b86862bc4d07ac2eaefea4d74d855de0f0bed5))
* **shared:** add project administration validators ([7d14884](https://github.com/grandcamel/jira-assistant-skills/commit/7d14884ed19f450575795ed9db77bdd96ebcce02))
* **shared:** add project management APIs and live integration test framework ([fc70ea3](https://github.com/grandcamel/jira-assistant-skills/commit/fc70ea3ea508688a00751205d9d2f94306a5c53b))
* **shared:** add version, component, notification, and changelog API methods ([f6fd03c](https://github.com/grandcamel/jira-assistant-skills/commit/f6fd03c2ebe4b5b8e1ab45da63e3bb4d758565de))
* **shared:** enhance core library with security and performance improvements ([6a4d2d7](https://github.com/grandcamel/jira-assistant-skills/commit/6a4d2d7c384a6a4bc1ba3b6a43b8b06b81e44aa1))
* **shared:** extend JiraClient with admin API methods ([93b56a1](https://github.com/grandcamel/jira-assistant-skills/commit/93b56a15871b8d15c26dc6fbbf87568216abe62c))


### Bug Fixes

* **.gitignore:** add metrics and memory database files to ignore list ([d6562c7](https://github.com/grandcamel/jira-assistant-skills/commit/d6562c7b36d6e9f9de0f7a3c59a050e2aa87b32d))
* **docs:** remove documentation for non-existent scripts ([93d8bd6](https://github.com/grandcamel/jira-assistant-skills/commit/93d8bd6de4912a83f39e093f99626283ee9a9dc1))
* **docs:** resolve broken markdown link patterns ([a6b301a](https://github.com/grandcamel/jira-assistant-skills/commit/a6b301a0292916013a8ab892365b47fc434d7f80))
* **jira-agile,shared:** add Agile API methods and fix runtime issues ([c33e08e](https://github.com/grandcamel/jira-assistant-skills/commit/c33e08e42d3a23dfa26b403b8216af6de1524767))
* **jira-agile:** correct API call patterns in scripts ([2caf956](https://github.com/grandcamel/jira-assistant-skills/commit/2caf9568f0e3c6982699dd4a01fb9122e6e6e52b))
* **jira-bulk,jira-dev,jira-fields,jira-ops:** fix live integration tests ([e77a7fb](https://github.com/grandcamel/jira-assistant-skills/commit/e77a7fb2daed126e61ffc7eea009faf155c2dd73))
* **jira-collaborate:** add proper mocking to get_comments tests (7/7 tests passing) ([9e60084](https://github.com/grandcamel/jira-assistant-skills/commit/9e60084dee6b6f09d0904cd92daf09da32f4f551))
* **jira-jsm,shared:** improve JSM live integration tests and add smart fixtures ([799d519](https://github.com/grandcamel/jira-assistant-skills/commit/799d519fef8fca39c2a90d11a4829e32f280fd1a))
* **jira-relationships:** correct link direction classification in get_links.py ([a463e3e](https://github.com/grandcamel/jira-assistant-skills/commit/a463e3ecce760973a765e1b178fcf5a1bb7060c2))
* **jira-search:** migrate to /rest/api/3/search/jql per CHANGE-2046 ([5c6dc10](https://github.com/grandcamel/jira-assistant-skills/commit/5c6dc1013b1fc4f7b218e763b524996985b6267e))
* **jira-search:** migrate to /rest/api/3/search/jql per CHANGE-2046 ([3e6c0a6](https://github.com/grandcamel/jira-assistant-skills/commit/3e6c0a654f32e59e73af9b90247269e0f32ad0d6))
* **jira-time:** fix conftest import in worklog lifecycle tests ([956551f](https://github.com/grandcamel/jira-assistant-skills/commit/956551f2525009356e9dee19a27a5b67367d0f19))
* **live-integration:** correct get_versions to get_project_versions in tests ([a485dec](https://github.com/grandcamel/jira-assistant-skills/commit/a485decc460951cc9688615a2578702705a11780))
* **shared,jira-lifecycle:** update search endpoint and fix issue assignment ([01fd846](https://github.com/grandcamel/jira-assistant-skills/commit/01fd84666068ae42a92f73b568af59a57d17a4c9))
* **shared,jira-relationships:** fix version creation and blocker link direction ([ccd5417](https://github.com/grandcamel/jira-assistant-skills/commit/ccd5417578439ed22c74f0c388ae41cfd99b6bf3))
* **shared,live-integration:** fix all live integration test failures (153/153 passing) ([dd8e7fd](https://github.com/grandcamel/jira-assistant-skills/commit/dd8e7fd4919622bc6e5b08daee917a6e80179c0c))
* **shared:** convert relative imports to absolute imports in shared library ([c36e471](https://github.com/grandcamel/jira-assistant-skills/commit/c36e471b0bc5fc745925518b7cb246dca1f6ef3b))
* **shared:** fix file upload Content-Type header issue ([b82b1c4](https://github.com/grandcamel/jira-assistant-skills/commit/b82b1c477f482d4a6eae368ebd8f3f5a4da3dd03))
* **shared:** handle string data in post method for watcher API ([2f1d7a3](https://github.com/grandcamel/jira-assistant-skills/commit/2f1d7a31c6c2d78ba709b70edf1c837de138ea4c))
* **shared:** update epic tests for simplified project templates ([22e1bb3](https://github.com/grandcamel/jira-assistant-skills/commit/22e1bb3faf69640e77e5a35473d2ac15b1ff92fd))
* **shared:** update sprint tests to verify via issue field ([ad83c31](https://github.com/grandcamel/jira-assistant-skills/commit/ad83c313477599b5dfba232bff9fd4925be9023f))
* **shared:** update user search test to use display name ([0562194](https://github.com/grandcamel/jira-assistant-skills/commit/0562194796f09909b05f2e563d751ab865e4813a))
* **test:** correct time tracking live integration tests ([1dcbb50](https://github.com/grandcamel/jira-assistant-skills/commit/1dcbb506f8faf6df9da4e10d66edfdfc69a50d55))

## Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).
