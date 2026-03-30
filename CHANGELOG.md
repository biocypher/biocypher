# Changelog

## [0.13.4](https://github.com/biocypher/biocypher/compare/biocypher-v0.13.3...biocypher-v0.13.4) (2026-03-30)


### Bug Fixes

* **neo4j:** version + shell handling in import ([#490](https://github.com/biocypher/biocypher/issues/490)) ([6f353a5](https://github.com/biocypher/biocypher/commit/6f353a5b846858f78e3e710ce8d6197d1c8bf11c))

## [0.13.3](https://github.com/biocypher/biocypher/compare/biocypher-v0.13.2...biocypher-v0.13.3) (2026-03-30)


### Miscellaneous

* trigger patch release ([#496](https://github.com/biocypher/biocypher/issues/496)) ([741dd32](https://github.com/biocypher/biocypher/commit/741dd32884c291449f3c273f5df51940aafe50ee))

## [0.13.2](https://github.com/biocypher/biocypher/compare/biocypher-v0.13.1...biocypher-v0.13.2) (2026-03-30)


### ⚠ BREAKING CHANGES

* **write:** file_format replaces rdf_format

### Features

* Add AnnData KG in memory representation ([#436](https://github.com/biocypher/biocypher/issues/436)) ([6836001](https://github.com/biocypher/biocypher/commit/6836001ad3e890ebe5006de7c8ef9cf73cb42dc8))
* add function for caching API requests and refine the args description ([4af6257](https://github.com/biocypher/biocypher/commit/4af6257a7e81e385932b940cd4e3ddbe5a8678f9))
* add methods to generate the import script suitable for windows ([c86ea56](https://github.com/biocypher/biocypher/commit/c86ea563558bd594501fe2d0df1f1393da40cb0a))
* dedicated graph class and simplified agent-usable API ([#459](https://github.com/biocypher/biocypher/issues/459)) ([56280ed](https://github.com/biocypher/biocypher/commit/56280edfcf526e00b0479f295af3fc08e7a27202))
* Extend NetworkX support ([#403](https://github.com/biocypher/biocypher/issues/403)) ([6cd7107](https://github.com/biocypher/biocypher/commit/6cd710747bd314a41efaac24c190964d3f7126fb))
* **git_testing_pipeline:** Include neo4j v5 and v4 ([f4de5f9](https://github.com/biocypher/biocypher/commit/f4de5f9115f2535c45d6d4e7f7d77caf87cc724f))
* **neo4j_v5_patch:** Detect n4j ver.-adapt syntax ([ef36f73](https://github.com/biocypher/biocypher/commit/ef36f739d228e06cb2e00a2211151bce33404d0d))
* **neo4j:** allow several labels sorting methods ([#410](https://github.com/biocypher/biocypher/issues/410)) ([f0e5d56](https://github.com/biocypher/biocypher/commit/f0e5d563b7f7fb0a9dafd20e47fc88c8c459f9fb))
* **neo4j:** supports Neo4j 5+ ([9534a5b](https://github.com/biocypher/biocypher/commit/9534a5b581adff7787145b7fb607a85de79f8e7e))
* Networkx and csv output adapter (writing to disk) ([cfc6523](https://github.com/biocypher/biocypher/commit/cfc6523148435e4da86bedffe9cb93076d88e837))
* select script name depending on host OS ([4c47b91](https://github.com/biocypher/biocypher/commit/4c47b9153087fb10d59c2c288c2a27fad94f136b))
* **test:** Database name location in import call ([38d6f85](https://github.com/biocypher/biocypher/commit/38d6f85bcc487875b0aa64779be4019c0be3a7bb))
* **test:** Import call functionality test ([2bb7258](https://github.com/biocypher/biocypher/commit/2bb72589e1c12cebb231baffbd0d52eda40e6e47))
* **tests:** Test import call construction ([03d4b25](https://github.com/biocypher/biocypher/commit/03d4b25c0ad2694014e5c9728a3e6f4900fdd4f7))
* **write:** OWL ([#412](https://github.com/biocypher/biocypher/issues/412)) ([2054ca5](https://github.com/biocypher/biocypher/commit/2054ca5d5e45068118a3427a80a06f35aff41f8b))


### Bug Fixes

* **_BatchWriter:** write all labels for edges ([#480](https://github.com/biocypher/biocypher/issues/480)) ([455f62d](https://github.com/biocypher/biocypher/commit/455f62db959c632cfa0b78764d66c7495924ad07))
* add newline to the powershell template based on pre-commit feedback ([a8576e6](https://github.com/biocypher/biocypher/commit/a8576e6a03958d4e550dfb208d050ea16dda04bc))
* **CICD:** Comment out MacOS Neo4j docker test ([3332e68](https://github.com/biocypher/biocypher/commit/3332e68a14c01dac920363b3247cf2642f8e737c))
* **core/write_import_call:** display an error message when no element is added ([#464](https://github.com/biocypher/biocypher/issues/464)) ([49c1ee1](https://github.com/biocypher/biocypher/commit/49c1ee17662802ba803b54043d9dafebbc0c4105))
* divide path in base and template paths ([495e5d1](https://github.com/biocypher/biocypher/commit/495e5d1288d387d44a561550d41441a952c3fd4d))
* fix default import call bin prefix, now the writer script doesn't have a default path ([6397f40](https://github.com/biocypher/biocypher/commit/6397f4061cf613e84be0d4519e1647176497ca05))
* fix path to the powershell template in test_neo4j.py ([9d00369](https://github.com/biocypher/biocypher/commit/9d003692d75fdd0ff6a540cf5d79853138dcb61d))
* **import call:** Add if-else statement ([42e0e32](https://github.com/biocypher/biocypher/commit/42e0e320f15029184870c6a4c75603fbb3242f1b))
* **import call:** Fix if-else statement ([559aa0b](https://github.com/biocypher/biocypher/commit/559aa0bd938a54228695d9254fad2e30a533094c))
* **import call:** Fix if-else statement ([bafeae9](https://github.com/biocypher/biocypher/commit/bafeae9def3f478c059115f5048223900aee84e5))
* **import_call:** Database name after import prefix ([4c12b9e](https://github.com/biocypher/biocypher/commit/4c12b9e22c19c1ed1166d4873039c1b35b9fdf56))
* neo4j CSV output not escaping quote character and cause import error ([#405](https://github.com/biocypher/biocypher/issues/405)) ([9b02016](https://github.com/biocypher/biocypher/commit/9b02016999ea54601840692c609da8a1a9510502))
* **neo4j_v5_patch:** Check neo4j v. - adapt syntax ([ea026b9](https://github.com/biocypher/biocypher/commit/ea026b9890775cc40c0d81a8f1b2fd3c702607c6))
* **neo4j:** v4 only supports --version while v5 supports both ([e6d6044](https://github.com/biocypher/biocypher/commit/e6d6044fdd99d9f79c4c74508454d7342f76ebe0))
* perform type checking to prevent import failure ([#458](https://github.com/biocypher/biocypher/issues/458)) ([b8a0fea](https://github.com/biocypher/biocypher/commit/b8a0fea04957d58c778a98d52de26493d411649a))
* **test-neo4j:** use the right variable in asserts ([c85e52f](https://github.com/biocypher/biocypher/commit/c85e52f11c667195476b68753032cbe1e0f256b8))
* **writer:** pass writer labels_order from config ([#479](https://github.com/biocypher/biocypher/issues/479)) ([5dffe6a](https://github.com/biocypher/biocypher/commit/5dffe6ac3d649b6c4867e4108bd6d4b4638bf05c))


### Documentation

* add tutorial 'Hands-On Protein Graphs with BioCypher (offline mode) and Neo4j' ([5387c71](https://github.com/biocypher/biocypher/commit/5387c71850132a2e86b78d35300973d5dcec0863))
* address first round of reviewer feedback ([9fd3f6d](https://github.com/biocypher/biocypher/commit/9fd3f6da09b4e9d4fdb20237c7b698e39bfe4e75))
* fix wrong script filename ([3b7c1ce](https://github.com/biocypher/biocypher/commit/3b7c1ce3764d115391083770b66b0b8e9990ee3f))
* more llm instructions ([027f890](https://github.com/biocypher/biocypher/commit/027f8903947029a2a953843bbc6cb45827ecc5e6))


### Miscellaneous

* override release version ([154ec52](https://github.com/biocypher/biocypher/commit/154ec526811b10d46cfdcde2f072ae2e81d33c6a))
