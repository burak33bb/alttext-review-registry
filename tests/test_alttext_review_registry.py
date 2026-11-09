import ast
import importlib.util
import json
import sys
import types
from pathlib import Path
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parents[1]
SOURCE = (ROOT / "contracts" / "alttext_review_registry.py").read_text(encoding="utf-8")


class Decorator:
    def __call__(self, function):
        return function


class TemporaryModule:
    def __init__(self, module):
        self.module = module
        self.previous = None

    def __enter__(self):
        self.previous = sys.modules.get("genlayer")
        sys.modules["genlayer"] = self.module

    def __exit__(self, exc_type, exc_value, traceback):
        if self.previous is None:
            sys.modules.pop("genlayer", None)
        else:
            sys.modules["genlayer"] = self.previous


def load_contract():
    class FakeContract:
        def __getattr__(self, name):
            if name == "reports":
                value = []
                setattr(self, name, value)
                return value
            raise AttributeError(name)

    public = types.SimpleNamespace(write=Decorator(), view=Decorator())
    nondet = types.SimpleNamespace(
        web=types.SimpleNamespace(
            render=lambda url, mode: "<img src='weather.png' alt=''>"
            if mode == "html"
            else "page screenshot or criterion text"
        ),
        exec_prompt=lambda prompt, images=None: "{}",
    )
    eq_principle = types.SimpleNamespace(
        prompt_comparative=lambda function, principle: function()
    )
    fake_genlayer = types.ModuleType("genlayer")
    fake_genlayer.gl = types.SimpleNamespace(
        Contract=FakeContract, public=public, nondet=nondet, eq_principle=eq_principle
    )
    fake_genlayer.DynArray = list
    fake_genlayer.u256 = int
    fake_genlayer.__all__ = ["gl", "DynArray", "u256"]
    with TemporaryModule(fake_genlayer):
        spec = importlib.util.spec_from_file_location(
            "alttext_contract_under_test", ROOT / "contracts" / "alttext_review_registry.py"
        )
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
    return module, nondet


def test_source_parses_and_uses_multimodal_independent_consensus():
    tree = ast.parse(SOURCE)
    assert any(
        isinstance(node, ast.ClassDef) and node.name == "AltTextReviewRegistry"
        for node in tree.body
    )
    assert "gl.eq_principle.prompt_comparative" in SOURCE
    assert 'gl.nondet.web.render(page_url, mode="screenshot")' in SOURCE
    assert "images=[screenshot]" in SOURCE
    assert "WCAG_GUIDANCE_URL" in SOURCE
    assert "DynArray()" not in SOURCE


def test_report_states_are_specific_and_do_not_claim_site_compliance():
    assert "ALT_SUPPORTED" in SOURCE
    assert "ALT_DEFECT_CONFIRMED" in SOURCE
    assert "DECORATIVE_EMPTY_ALT" in SOURCE
    assert "NEEDS_REVIEW" in SOURCE
    assert "not a site-wide accessibility audit" in SOURCE
    assert "Never claim overall WCAG" in SOURCE


def test_website_domain_is_exact_and_https_only():
    module, _ = load_contract()
    assert module._normalize_domain("https://www.w3.org/WAI/") == "w3.org"
    assert module._is_allowed_page("https://www.w3.org/WAI/page", "w3.org")
    assert not module._is_allowed_page("http://www.w3.org/WAI/page", "w3.org")
    assert not module._is_allowed_page("https://w3.org.attacker.example/page", "w3.org")


def test_assessment_schema_rejects_unexpected_fields_and_invalid_types():
    module, _ = load_contract()
    valid = {
        "image_role": "INFORMATIVE",
        "alt_attribute_present": True,
        "observed_alt_text": "Weather forecast",
        "assessment": "ADEQUATE",
        "image_locator": "weather image near forecast heading",
        "evidence": ["<img src='weather.png' alt='Weather forecast'>"],
        "reasoning": "The concise alternative conveys the image's purpose.",
    }
    assert module._validate_assessment(valid) == valid
    invalid = dict(valid, hidden_instruction="not allowed")
    try:
        module._validate_assessment(invalid)
    except ValueError:
        pass
    else:
        raise AssertionError("Unexpected schema field was accepted.")


def test_informative_defect_is_reported_after_consensus():
    module, nondet = load_contract()
    contract = module.AltTextReviewRegistry("w3.org")
    result = {
        "image_role": "INFORMATIVE",
        "alt_attribute_present": False,
        "observed_alt_text": "",
        "assessment": "DEFECTIVE",
        "image_locator": "weather image of cloud and sun near page top",
        "evidence": ["<img src='weather.png'>"],
        "reasoning": "The image conveys the weather and has no text alternative.",
    }
    nondet.exec_prompt = lambda prompt, images=None: json.dumps(result)

    report = contract.review_alt_text(
        "https://www.w3.org/WAI/demos/bad/before/home",
        "weather image of cloud and sun near the top",
        "",
        "The image illustrates current weather information.",
    )

    assert report["decision"] == "ALT_DEFECT_CONFIRMED"
    assert report["id"] == 1
    assert contract.get_report_count() == 1
    assert contract.get_latest_report()["reason_code"] == "ALTERNATIVE_DEFECT_SUPPORTED_BY_PAGE_EVIDENCE"


def test_adequate_informative_alt_is_not_called_a_defect():
    module, nondet = load_contract()
    contract = module.AltTextReviewRegistry("w3.org")
    result = {
        "image_role": "INFORMATIVE",
        "alt_attribute_present": True,
        "observed_alt_text": "Citylights: your access to the city.",
        "assessment": "ADEQUATE",
        "image_locator": "site logo near page header",
        "evidence": ["alt='Citylights: your access to the city.'"],
        "reasoning": "The alternative communicates the image's site identity.",
    }
    nondet.exec_prompt = lambda prompt, images=None: json.dumps(result)

    report = contract.review_alt_text(
        "https://w3.org/WAI/demos/bad/before/home",
        "citylights site logo",
        "Citylights: your access to the city.",
    )

    assert report["decision"] == "ALT_SUPPORTED"
    assert contract.get_report(1)["observed_alt_text"] == "Citylights: your access to the city."


def test_decorative_image_requires_explicit_empty_alt():
    module, nondet = load_contract()
    contract = module.AltTextReviewRegistry("w3.org")
    result = {
        "image_role": "DECORATIVE",
        "alt_attribute_present": True,
        "observed_alt_text": "",
        "assessment": "ADEQUATE",
        "image_locator": "decorative divider image",
        "evidence": ["<img src='divider.png' alt=''>"],
        "reasoning": "The image adds no information and has an explicit empty alt.",
    }
    nondet.exec_prompt = lambda prompt, images=None: json.dumps(result)

    report = contract.review_alt_text(
        "https://w3.org/WAI/example",
        "decorative divider image",
        "",
    )

    assert report["decision"] == "DECORATIVE_EMPTY_ALT"


def test_reported_alt_mismatch_and_ambiguous_image_fail_closed():
    module, nondet = load_contract()
    contract = module.AltTextReviewRegistry("w3.org")
    result = {
        "image_role": "INFORMATIVE",
        "alt_attribute_present": True,
        "observed_alt_text": "Actual text on page",
        "assessment": "ADEQUATE",
        "image_locator": "image beside the main heading",
        "evidence": ["alt='Actual text on page'"],
        "reasoning": "The caller's claimed value does not match the page.",
    }
    nondet.exec_prompt = lambda prompt, images=None: json.dumps(result)
    mismatch = contract.review_alt_text("https://w3.org/example", "hero image", "Claimed text")
    assert mismatch["decision"] == "NEEDS_REVIEW"
    assert mismatch["reason_code"] == "CALLER_ALT_TEXT_DIFFERS_FROM_PAGE"

    result.update(image_role="UNKNOWN", assessment="INCONCLUSIVE")
    ambiguous = contract.review_alt_text("https://w3.org/example", "unclear image", "Claimed text")
    assert ambiguous["decision"] == "NEEDS_REVIEW"


def test_off_domain_input_is_rejected_before_consensus():
    module, nondet = load_contract()
    contract = module.AltTextReviewRegistry("w3.org")
    called = {"prompt": False}
    nondet.exec_prompt = lambda prompt, images=None: called.update(prompt=True) or "{}"
    try:
        contract.review_alt_text("https://attacker.example/page", "image", "")
    except ValueError as error:
        assert "configured HTTPS domain" in str(error)
    else:
        raise AssertionError("Off-domain page was accepted.")
    assert not called["prompt"]
    assert contract.get_report_count() == 0


def test_domain_normalization_helper_uses_parsed_hostname():
    value = "https://www.w3.org/WAI/demos/bad/before/home"
    assert urlparse(value).hostname == "www.w3.org"
