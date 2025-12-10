import base64
import hashlib
import json
import logging
import secrets
import urllib.parse
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Iterable

import requests

logger = logging.getLogger(__name__)

AUTH_URL = "https://cloud.ouraring.com/oauth/authorize"
TOKEN_URL = "https://api.ouraring.com/oauth/token"
DEFAULT_SCOPES = ["email", "personal", "daily", "heartrate", "spo2", "stress"]
TOKEN_EXPIRY_MARGIN = timedelta(seconds=30)


class StaticTokenProvider:
    """Simple wrapper for legacy personal access tokens."""

    def __init__(self, token: str):
        self.token = token

    def get_access_token(self, force_refresh: bool = False) -> str:  # noqa: ARG002
        return self.token

    def refresh_access_token(self) -> bool:
        return False


class OAuthTokenManager:
    """Handles Oura OAuth2 Authorization Code + PKCE flow with persisted tokens."""

    def __init__(
        self,
        client_id: str,
        client_secret: str | None,
        redirect_uri: str,
        scopes: Iterable[str] | None = None,
        token_path: str | Path | None = None,
        initial_auth_code: str | None = None,
        stdin_is_interactive: bool | None = None,
    ):
        self.client_id = client_id
        self.client_secret = client_secret
        self.redirect_uri = redirect_uri
        self.scopes = list(scopes) if scopes else DEFAULT_SCOPES
        self.token_path = (
            Path(token_path).expanduser()
            if token_path
            else Path.home() / ".config" / "oura-exporter" / "oauth_token.json"
        )
        self.pending_auth_path = self.token_path.parent / "pending_auth.json"
        self._code_verifier: str | None = None
        self.token: dict | None = self._load_token()
        self.initial_auth_code = initial_auth_code
        self.stdin_is_interactive = (
            sys.stdin.isatty() if stdin_is_interactive is None else stdin_is_interactive
        )

    def get_access_token(self, force_refresh: bool = False) -> str:
        if self.token and not force_refresh and not self._token_expired(self.token):
            return self.token["access_token"]

        if self.token and self.token.get("refresh_token"):
            if self.refresh_access_token():
                return self.token["access_token"]
            logger.warning("Refresh token failed; falling back to new authorization flow.")

        if not self.client_id:
            raise RuntimeError("Oura client_id is missing. Set OURA_CLIENT_ID.")

        self._interactive_authorization()
        if not self.token:
            raise RuntimeError("Authorization did not yield an access token.")
        return self.token["access_token"]

    def refresh_access_token(self) -> bool:
        if not self.token or not self.token.get("refresh_token"):
            return False

        payload = {
            "grant_type": "refresh_token",
            "refresh_token": self.token["refresh_token"],
        }
        response = self._request_token(payload)
        if not response:
            return False
        self._store_token(response)
        logger.info("Refreshed Oura access token.")
        return True

    def _interactive_authorization(self) -> None:
        self._code_verifier, code_challenge = self._prepare_pkce()
        state = self._generate_state()
        auth_url = self._build_authorize_url(code_challenge, state)

        logger.info("No usable token found. Complete OAuth consent to proceed.")
        logger.info("Open the following URL in your browser to authorize Oura access:")
        logger.info(auth_url)
        logger.info("After granting access, copy the `code` query parameter from the redirected URL and paste it below.")

        code = self._get_authorization_code(auth_url)
        if not code:
            raise RuntimeError("No authorization code provided; cannot continue.")

        token_response = self._exchange_code_for_tokens(code)
        if not token_response:
            raise RuntimeError("Failed to exchange authorization code for tokens.")
        self._store_token(token_response)

    def _exchange_code_for_tokens(self, code: str) -> dict | None:
        payload = {
            "grant_type": "authorization_code",
            "code": code,
            "redirect_uri": self.redirect_uri,
        }
        if not self._code_verifier:
            logger.error("Code verifier missing; cannot complete PKCE flow.")
            return None
        payload["code_verifier"] = self._code_verifier

        return self._request_token(payload)

    def _request_token(self, payload: dict) -> dict | None:
        data = {"client_id": self.client_id, **payload}
        auth = None
        if self.client_secret:
            auth = (self.client_id, self.client_secret)

        try:
            response = requests.post(
                TOKEN_URL,
                data=data,
                auth=auth,
                timeout=15,
            )
        except requests.exceptions.RequestException as exc:
            logger.error("Token endpoint request failed: %s", exc)
            return None

        if response.status_code != 200:
            logger.error(
                "Token endpoint returned %s: %s",
                response.status_code,
                response.text,
            )
            return None

        try:
            return response.json()
        except ValueError:
            logger.error("Token endpoint did not return JSON: %s", response.text)
            return None

    def _token_expired(self, token: dict) -> bool:
        expires_at = token.get("expires_at")
        if not expires_at:
            return True
        try:
            expiry = datetime.fromisoformat(expires_at)
        except ValueError:
            return True
        return expiry <= datetime.now(timezone.utc) + TOKEN_EXPIRY_MARGIN

    def _store_token(self, token_payload: dict) -> None:
        expires_in = token_payload.get("expires_in")
        if not expires_in:
            raise RuntimeError("Token payload missing expires_in.")

        refresh_token = token_payload.get("refresh_token")
        if not refresh_token and self.token and self.token.get("refresh_token"):
            refresh_token = self.token["refresh_token"]

        self.token = {
            "access_token": token_payload["access_token"],
            "refresh_token": refresh_token,
            "expires_at": (
                datetime.now(timezone.utc) + timedelta(seconds=int(expires_in))
            ).isoformat(),
        }

        self.token_path.parent.mkdir(parents=True, exist_ok=True)
        with self.token_path.open("w", encoding="utf-8") as fp:
            json.dump(self.token, fp, indent=2)
        try:
            self.token_path.chmod(0o600)
        except OSError:
            logger.debug("Could not adjust permissions for %s", self.token_path)
        self._clear_pending_auth()

    def _load_token(self) -> dict | None:
        if not self.token_path.exists():
            return None
        try:
            with self.token_path.open(encoding="utf-8") as fp:
                return json.load(fp)
        except (OSError, ValueError) as exc:
            logger.warning("Could not read token file %s: %s", self.token_path, exc)
            return None

    def _build_authorize_url(self, code_challenge: str, state: str) -> str:
        params = {
            "response_type": "code",
            "client_id": self.client_id,
            "redirect_uri": self.redirect_uri,
            "scope": " ".join(self.scopes),
            "state": state,
            "code_challenge": code_challenge,
            "code_challenge_method": "S256",
        }
        return f"{AUTH_URL}?{urllib.parse.urlencode(params)}"

    @staticmethod
    def _generate_code_verifier() -> str:
        return base64.urlsafe_b64encode(secrets.token_bytes(64)).decode().rstrip("=")

    @staticmethod
    def _generate_code_challenge(code_verifier: str) -> str:
        digest = hashlib.sha256(code_verifier.encode("utf-8")).digest()
        return base64.urlsafe_b64encode(digest).decode().rstrip("=")

    @staticmethod
    def _generate_state() -> str:
        return secrets.token_urlsafe(32)

    @staticmethod
    def _extract_code(value: str) -> str | None:
        try:
            parsed = urllib.parse.urlparse(value)
            query_params = urllib.parse.parse_qs(parsed.query)
            if "code" in query_params:
                return query_params["code"][0]
        except Exception:  # noqa: BLE001
            logger.debug("Could not parse value as URL, treating as raw code.")

        return value if value else None

    def _get_authorization_code(self, auth_url: str) -> str | None:
        if self.initial_auth_code:
            if not self._code_verifier:
                # Attempt to reuse previously saved PKCE verifier (for two-step / headless flows).
                pending = self._load_pending_auth()
                if pending and pending.get("code_verifier"):
                    self._code_verifier = pending["code_verifier"]
            if not self._code_verifier:
                raise RuntimeError("No stored PKCE verifier found; re-run once to print the auth URL, then supply OURA_AUTH_CODE from that same run.")
            code = self._extract_code(self.initial_auth_code)
            if code:
                return code
            raise RuntimeError("Provided OURA_AUTH_CODE could not be parsed.")

        if not self.stdin_is_interactive:
            raise RuntimeError(
                "No interactive stdin available. Re-run with a TTY or set OURA_AUTH_CODE "
                "to the `code` from the redirected URL.\n"
                f"Authorization URL: {auth_url}"
            )

        code_input = input("Authorization code (from the redirected URL): ").strip()
        return self._extract_code(code_input)

    def _prepare_pkce(self) -> tuple[str, str]:
        if self._code_verifier:
            return self._code_verifier, self._generate_code_challenge(self._code_verifier)

        pending = self._load_pending_auth()
        if pending and pending.get("code_verifier"):
            self._code_verifier = pending["code_verifier"]
            return self._code_verifier, self._generate_code_challenge(self._code_verifier)

        self._code_verifier = self._generate_code_verifier()
        self._save_pending_auth(self._code_verifier)
        return self._code_verifier, self._generate_code_challenge(self._code_verifier)

    def _load_pending_auth(self) -> dict | None:
        if not self.pending_auth_path.exists():
            return None
        try:
            with self.pending_auth_path.open(encoding="utf-8") as fp:
                return json.load(fp)
        except (OSError, ValueError) as exc:
            logger.warning("Could not read pending auth file %s: %s", self.pending_auth_path, exc)
            return None

    def _save_pending_auth(self, code_verifier: str) -> None:
        payload = {
            "code_verifier": code_verifier,
            "redirect_uri": self.redirect_uri,
            "scopes": self.scopes,
            "created_at": datetime.now(timezone.utc).isoformat(),
        }
        self.pending_auth_path.parent.mkdir(parents=True, exist_ok=True)
        try:
            with self.pending_auth_path.open("w", encoding="utf-8") as fp:
                json.dump(payload, fp, indent=2)
            self.pending_auth_path.chmod(0o600)
        except OSError as exc:
            logger.debug("Could not persist pending auth to %s: %s", self.pending_auth_path, exc)

    def _clear_pending_auth(self) -> None:
        try:
            self.pending_auth_path.unlink()
        except FileNotFoundError:
            return
        except OSError as exc:
            logger.debug("Could not remove pending auth file %s: %s", self.pending_auth_path, exc)
