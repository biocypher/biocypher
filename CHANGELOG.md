# Changelog

## [0.15.2](https://github.com/biocypher/biocypher/compare/biocypher-v0.15.1...biocypher-v0.15.2) (2026-06-22)


### Bug Fixes

* **neo4j:** CSV escaping quote character ([#572](https://github.com/biocypher/biocypher/issues/572)) ([c4ef798](https://github.com/biocypher/biocypher/commit/c4ef798d8de9cb06960bbd8aae1ce10f24024213))

## [0.15.1](https://github.com/biocypher/biocypher/compare/biocypher-v0.15.0...biocypher-v0.15.1) (2026-06-01)


### Bug Fixes

* **batch_writer:** infer typed array annotations for list properties not in schema ([#533](https://github.com/biocypher/biocypher/issues/533)) ([2cd4042](https://github.com/biocypher/biocypher/commit/2cd404241c102fecbe62d03d70d07514e4257c43))
* **mapping:** correctly merge parent exclude_properties in vertical inheritance ([#542](https://github.com/biocypher/biocypher/issues/542)) ([4c78eff](https://github.com/biocypher/biocypher/commit/4c78effe5e758916fe94551296f1cc2796010e2e))
* **sqlite:** add set -e to import script and skip test when sqlite3 CLI absent ([#541](https://github.com/biocypher/biocypher/issues/541)) ([4c09af3](https://github.com/biocypher/biocypher/commit/4c09af307486e05c0a157828d31ea308b0466446))

## [0.15.0](https://github.com/biocypher/biocypher/compare/biocypher-v0.14.1...biocypher-v0.15.0) (2026-05-29)


### Features

* **batch_writer:** stream edge processing in offline mode to eliminate unbounded memory usage ([#539](https://github.com/biocypher/biocypher/issues/539)) ([206145b](https://github.com/biocypher/biocypher/commit/206145b7091a391c9ebaf4dd3d6749973729fe7d))


### Bug Fixes

* **core:** _add_edges called non-existent method and wrong driver method ([#538](https://github.com/biocypher/biocypher/issues/538)) ([c58c75b](https://github.com/biocypher/biocypher/commit/c58c75b11a6a04a541e3aba857f6378810b6decd))


### Documentation

* clarify Neo4j import file prefix ([#535](https://github.com/biocypher/biocypher/issues/535)) ([b2ec20f](https://github.com/biocypher/biocypher/commit/b2ec20f48f4ef3eb6bf4372c6f5edcba659014d9))
* clarify Ruff development workflow ([#536](https://github.com/biocypher/biocypher/issues/536)) ([1c91dfc](https://github.com/biocypher/biocypher/commit/1c91dfc424d7df33df15a3ca92afb0401f13453b))
* **config:** add merge_nodes example to tail_ontologies in biocypher_config.yaml ([#532](https://github.com/biocypher/biocypher/issues/532)) ([f761fdb](https://github.com/biocypher/biocypher/commit/f761fdbf6b98a5049000c1ea63e0fdee619df69d))

## [0.14.1](https://github.com/biocypher/biocypher/compare/biocypher-v0.14.0...biocypher-v0.14.1) (2026-05-26)


### Bug Fixes

* **batch_writer:** stringify list elements before joining in _write_array_string ([#524](https://github.com/biocypher/biocypher/issues/524)) ([9f2b153](https://github.com/biocypher/biocypher/commit/9f2b1531133e3b7106fac4c1a6bfc7ca61f85c96))
* **create:** replace elif with if for reserved keyword checks in BioCypherEdge ([#526](https://github.com/biocypher/biocypher/issues/526)) ([06f75c1](https://github.com/biocypher/biocypher/commit/06f75c1e7cc71f15f962e29285e6832a6cba8a71))
* **get:** treat lifetime=0 as permanent cache (never re-download) ([#525](https://github.com/biocypher/biocypher/issues/525)) ([fc6b092](https://github.com/biocypher/biocypher/commit/fc6b092a4f3438ba8a3da2eec50f5153eb29c165))
* **parse_label:** guard against IndexError when label has no compliant characters ([#529](https://github.com/biocypher/biocypher/issues/529)) ([a8a4f8e](https://github.com/biocypher/biocypher/commit/a8a4f8ef1d1815c2a023a617bed3a0e1cb0be51e))
* **translate:** require 'version' and accept 'license' for edges in strict mode ([#527](https://github.com/biocypher/biocypher/issues/527)) ([e902ea3](https://github.com/biocypher/biocypher/commit/e902ea3a484a5ea799b5d3b203d33885e126425a))

## [0.14.0](https://github.com/biocypher/biocypher/compare/biocypher-v0.13.6...biocypher-v0.14.0) (2026-05-21)


### Features

* **core:** allow head_ontology: null for headless builds ([#523](https://github.com/biocypher/biocypher/issues/523)) ([1bcda5d](https://github.com/biocypher/biocypher/commit/1bcda5dc5ba0ae837bf4448c8a8b7351326fd96e))
* **mapping:** accept 'namespace' as alias for 'preferred_id'; deprecate 'preferred_id' in schema config ([#519](https://github.com/biocypher/biocypher/issues/519)) ([87806c1](https://github.com/biocypher/biocypher/commit/87806c182cab9eab4a943709d5a6f458d5344cd4))


### Bug Fixes

* **batch_writer:** prevent schema mutation in strict-mode edge writes; fix f-string in translate error ([#517](https://github.com/biocypher/biocypher/issues/517)) ([9cd7c64](https://github.com/biocypher/biocypher/commit/9cd7c64b83bc328f1a49d83c7008b9ecf75b9711))
* **batch_writer:** write boolean properties as lowercase true/false for Neo4j ([#510](https://github.com/biocypher/biocypher/issues/510)) ([95e3021](https://github.com/biocypher/biocypher/commit/95e3021dcade2e2d605e4888501cd5cdd3abbf22))
* **config:** properly merge all three config levels in read_config() ([#515](https://github.com/biocypher/biocypher/issues/515)) ([da251fd](https://github.com/biocypher/biocypher/commit/da251fdf2c5917ea40fab0391afda1ff666d0cba))
* **core:** allow pandas and tabular as dbms aliases in offline mode ([#513](https://github.com/biocypher/biocypher/issues/513)) ([7e3ee26](https://github.com/biocypher/biocypher/commit/7e3ee269345ea4b6b7f5d2cbf00463a8bd006332))
* **create:** skip .replace() for non-string items in list properties ([#518](https://github.com/biocypher/biocypher/issues/518)) ([49b5756](https://github.com/biocypher/biocypher/commit/49b5756f0729c3684f4191603524c9d5f86bc75c))
* **mapping:** deprecate 'label_in_input' in favour of 'input_label' ([#521](https://github.com/biocypher/biocypher/issues/521)) ([26a1c1f](https://github.com/biocypher/biocypher/commit/26a1c1f3b3de648510067f2a2690aadbe42a3d41))

## [0.13.6](https://github.com/biocypher/biocypher/compare/biocypher-v0.13.5...biocypher-v0.13.6) (2026-05-09)


### Bug Fixes

* **get:** preserve query params in cache filenames; hash full URL when too long ([#507](https://github.com/biocypher/biocypher/issues/507)) ([538b8b3](https://github.com/biocypher/biocypher/commit/538b8b328df0810a9d4f40a239c284ec5654e0e0))


### Documentation

* **create:** fix BioCypherEdge docstring inaccuracies ([#508](https://github.com/biocypher/biocypher/issues/508)) ([e23c68c](https://github.com/biocypher/biocypher/commit/e23c68c80b76eca1976288677c5bacdbaf7fb9ee)), closes [#391](https://github.com/biocypher/biocypher/issues/391)
* document write_schema_info() workflow for BioChatter integration ([#499](https://github.com/biocypher/biocypher/issues/499)) ([9cb0042](https://github.com/biocypher/biocypher/commit/9cb004265a33100cd3909ada3c53208d7aac9dee))

## [0.13.5](https://github.com/biocypher/biocypher/compare/biocypher-v0.13.4...biocypher-v0.13.5) (2026-05-07)


### Bug Fixes

* handle empty iterables in write_nodes/write_edges without crashing ([#504](https://github.com/biocypher/biocypher/issues/504)) ([3b30e7b](https://github.com/biocypher/biocypher/commit/3b30e7be0a101ad5d9b8d732c9cb399c4ea60034))

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
