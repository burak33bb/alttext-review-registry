# Submission Summary

**AltText Review Registry** is a reusable GenLayer Intelligent Contract for reviewing one source-linked web-image text alternative under WCAG 2.2 SC 1.1.1. It is not a site-wide accessibility score or certification.

For each finding, the leader and validators independently fetch the page HTML, render a screenshot, and read the W3C criterion guidance. A comparative equivalence principle requires agreement on the identified image, its role, whether its `alt` attribute exists, the exact observed alt value, and the adequacy assessment. Deterministic contract logic checks that the caller's reported alt still matches the live page, distinguishes informative/functional from decorative images, stores bounded append-only findings, and fails closed to `NEEDS_REVIEW` when evidence is ambiguous.

The repository includes the contract, tests, an example using W3C's documented missing-alt demo, and explicit limitations. The primitive does not certify overall accessibility or provide legal advice.
