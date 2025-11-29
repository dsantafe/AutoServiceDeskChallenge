import json
import os
from functools import lru_cache

@lru_cache
def _load_profiles() -> dict:
    base_dir = os.path.dirname(os.path.abspath(__file__))
    json_path = os.path.join(base_dir, "..", "data", "user_profiles.json")
    with open(json_path, "r", encoding="utf-8") as f:
        return json.load(f)


def get_user_profile(email: str) -> dict:
    """
    Returns a user profile dict with keys: role, area, trust_level.
    Falls back to '_default' if the email is not found.
    """
    profiles = _load_profiles()
    email_key = (email or "").lower()
    profile = profiles.get(email_key, profiles.get("_default", {}))
    return {
        "role": profile.get("role", "Unknown"),
        "area": profile.get("area", "Unknown"),
        "trust_level": profile.get("trust_level", 1),
    }
