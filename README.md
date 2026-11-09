# AltText Review Registry

AltText Review Registry is a standalone GenLayer Intelligent Contract primitive for reviewing one reported image alternative on one public web page. It is designed for accessibility auditors and maintainers who need a reproducible, source-linked finding rather than a site-wide AI score.

The registry inspects the page HTML and a rendered screenshot together with the W3C WCAG 2.2 guidance for non-text content. Validators independently fetch the page and guidance, inspect the same identified image, and reach comparative consensus on its role, exact current `alt` text, and whether that alternative is adequate. The contract checks that the caller-reported alt text still matches the live page, then stores a bounded report with evidence and a conservative decision.

## Decisions

- `ALT_SUPPORTED`: validators agreed that the actual alternative adequately conveys the informative or functional image's purpose.
- `ALT_DEFECT_CONFIRMED`: validators agreed that an image requiring an alternative has a defective or missing alternative.
- `DECORATIVE_EMPTY_ALT`: validators agreed that the image is decorative and its HTML has an explicit empty `alt` attribute.
- `NEEDS_REVIEW`: source text differs from the caller's report, the image cannot be identified reliably, or the validators cannot establish a clear result.

This contract reviews one image finding only. It does not certify a website, make a legal-compliance determination, or replace a full human accessibility audit. W3C guidance distinguishes informative, functional, and decorative images; the contract preserves that distinction rather than treating every image the same.

## State Design

- `site_domain`: deployment-time HTTPS domain allowlist for page review.
- `reports`: append-only JSON history, bounded to 100 findings.
- `latest_report`: cached most recent finding for simple inspection.
- Each report stores the page, image hint, caller-reported and observed alt text, image role, reviewer assessment, conservative decision, evidence excerpts, and reasoning.

## Consensus Design

`review_alt_text(page_url, image_hint, reported_alt_text, purpose_context)` independently renders page HTML and a screenshot on the leader and validators. It also fetches W3C's WCAG 2.2 Understanding Non-text Content page. The comparative principle requires agreement on image role, whether the `alt` attribute exists, the exact observed alt text, and the criterion-level assessment. Validators must identify the same image from the hint; ambiguity is not converted into a positive finding.

After consensus, deterministic code checks the reported alt against the live observed value. It records `NEEDS_REVIEW` on mismatch, maps informative/functional assessments to supported or confirmed-defect decisions, and only accepts an empty alt as `DECORATIVE_EMPTY_ALT` when the attribute is present and the image is classified decorative.

Only compact excerpts and the structured result are written to state. The page screenshot itself is not stored on-chain.

## Example Deployment and Call

For a reproducible demonstration, use the W3C WAI Before and After Demo, whose own accessibility guidance documents missing alt text on its weather image.

```text
site_domain: w3.org
page_url: https://www.w3.org/WAI/demos/bad/before/home
image_hint: The weather image of the cloud and sun near the top of the page
reported_alt_text:
purpose_context: The image conveys weather information and is not decorative.
```

The documented missing-alt case should produce `ALT_DEFECT_CONFIRMED`; a validator that cannot identify the same image must return an inconclusive result, which the contract stores as `NEEDS_REVIEW`.

## Limits

- The page must be public, HTTPS, and within the configured domain. It must render successfully for validators.
- Dynamic content, lazy-loaded images, responsive variants, and CSS-generated imagery may be inconclusive.
- Image purpose depends on page context. The caller's purpose context is unverified input; validators must inspect the actual page and screenshot.
- `ALT_SUPPORTED` covers only the identified image on the captured page state. It says nothing about other accessibility criteria, states, viewports, or the overall site.
- Vision-capable validator models are required for screenshot analysis.

## Tests

```powershell
python -m pip install -r requirements-dev.txt
python -m pytest tests -q
```

The tests exercise schema validation, exact-domain URL checks, outcome mapping, source mismatch handling, fail-closed ambiguity, and the mocked GenLayer consensus path. A successful unit test is not a substitute for a live Studio transaction.
