# Changelog
All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](http://keepachangelog.com/en/1.0.0/)
and this project adheres to [Semantic Versioning](http://semver.org/spec/v2.0.0.html).

## [Unreleased]
### Added
 - [Fix] Delete adding minute in validation data

## [10.0.1.3.2] - 2019-12-12
### Added
 - [Imp] Add blockUI on pay button

## [10.0.1.3.1] - 2019-09-19
### Added
 - [Fix] Check if payment transaction is already sent to TipiRégie webservice and recreate it in this case.
 - [Fix] Set real validation datetime from TipiRégie webservice information

## [10.0.1.3.0] - 2019-07-19
### Added
- Add progression information on migration script
- Add cron to check all draft tipiregie transactions
- Add email to notify company about the result of cron update, deactivate by default

## [10.0.1.2.3] - 2018-03-08
### Added
- Change amount calculation to avoid rounding issues

## [10.0.1.2.2] - 2018-12-26
### Added
- Delete useless dependency

## [10.0.1.2.1] - 2018-12-03
### Added
- If transaction is already done, we don't try to validate again.

## [10.0.1.2.0] - 2018-09-12
### Added
- Rework operation identifier recovery from TipiRegie webservice and set it functional with website_sale and website_payment modules.

## [10.0.1.1.1] - 2018-05-16
### Added
- Get idOp from DGFIP if current reference is not '/'
- Change '/' to '  slash  ' cause TipiRegie web service doesn't accept special chars
- Add gitignore

## [10.0.1.1.0] - 2018-04-06
### Added
- Add parameter for return URL

## [10.0.1.0.2] - 2018-01-02
### Added
- Add activation mode in test environment to validate the TipiRégie workflow close to DGFIP

## [10.0.1.0.1] - 2017-10-20
### Added
- Tipi server checks when customer_number and website_published fields are edited

## [10.0.1.0.0] - 2017-10-16
### Added
- Tipi Régie payment acquirer module

[10.0.1.0.1]: https://github.com/Horanet/payment_tipiregie/compare/10.0.1.0.0...10.0.1.0.1
[10.0.1.0.2]: https://github.com/Horanet/payment_tipiregie/compare/10.0.1.0.1...10.0.1.0.2
[10.0.1.1.0]: https://github.com/Horanet/payment_tipiregie/compare/10.0.1.0.2...10.0.1.1.0
[10.0.1.1.1]: https://github.com/Horanet/payment_tipiregie/compare/10.0.1.1.0...10.0.1.1.1
[10.0.1.2.0]: https://github.com/Horanet/payment_tipiregie/compare/10.0.1.1.1...10.0.1.2.0
[10.0.1.2.1]: https://github.com/Horanet/payment_tipiregie/compare/10.0.1.2.0...10.0.1.2.1
[10.0.1.2.2]: https://github.com/Horanet/payment_tipiregie/compare/10.0.1.2.1...10.0.1.2.2
[10.0.1.2.3]: https://github.com/Horanet/payment_tipiregie/compare/10.0.1.2.2...10.0.1.2.3
[10.0.1.3.0]: https://github.com/Horanet/payment_tipiregie/compare/10.0.1.2.3...10.0.1.3.0
[10.0.1.3.1]: https://github.com/Horanet/payment_tipiregie/compare/10.0.1.3.0...10.0.1.3.1
[10.0.1.3.2]: https://github.com/Horanet/payment_tipiregie/compare/10.0.1.3.1...10.0.1.3.2
[Unreleased]: https://github.com/Horanet/payment_tipiregie/compare/10.0.1.3.2...dev