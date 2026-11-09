# Submission Summary

**AltText Review Registry** is a reusable GenLayer Intelligent Contract for reviewing one source-linked web-image text alternative under WCAG 2.2 SC 1.1.1. It is not a site-wide accessibility score or certification.

For each finding, the leader and validators independently fetch the page HTML and render a screenshot, using a pinned, source-linked summary of the W3C criterion. A comparative equivalence principle requires agreement on the identified image, its role, whether its `alt` attribute exists, the exact observed alt value, and the adequacy assessment. Deterministic contract logic checks that the caller's reported alt still matches the live page, distinguishes informative/functional from decorative images, stores bounded append-only findings, and fails closed to `NEEDS_REVIEW` when evidence is ambiguous.

The repository includes the contract, tests, a reproducible Microsoft Edge demo case with documented missing-alt findings, and explicit limitations. The primitive does not certify overall accessibility or provide legal advice.
