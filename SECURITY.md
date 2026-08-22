# Security Policy

## Reporting a Vulnerability

Please report security issues through [GitHub's private security advisory form](https://github.com/jwilson411/rivulet-dispatch/security/advisories/new) rather than a public issue. Private advisories give us a chance to fix the problem before it is disclosed.

Include the affected version or commit, steps to reproduce, and what an attacker gains.

## Scope

rivulet-dispatch is a local library. It has no network stack and does not store, load, or transmit secrets. You pass a message and a team; you get back who should speak. The optional LLM fallback is an injected callable. This package never opens a socket and never talks to a model vendor.

An attacker who already controls the process calling the library is out of scope.

## Supported versions

Only the latest release receives security fixes.
