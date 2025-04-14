# Changelog
All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/), and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## Unreleased

## v0.10.0

* add `watchdog` demo.
* change linting to `ruff`
* add timeout for `set_axis_state` and `wait_for_heartbeat`
* add `wait_for_heartbeat()` - used used to get status before checking for errors.


## v0.9.2

* cancel task on stop
* add `roc` parameter to `mock`

## v0.8.0

* add `set_axis_state_no_wait`


## v0.7.0

* add amplitude parameter to `demo` code
* split udp feedback per axis
* remove polling example
* add refererence to `ODriveCAN` in `.feedback_callback`
* rename `.position_callback` to `.feedback_callback`


## v0.6.1

* Beta release
* Updated examples and docs
* Major refactoring
* Made `OdriveMock` behave realistically.



## v0.5.0

* implemented full dbc interface
* ramp velocity control demo
* position control demo with different input modes

