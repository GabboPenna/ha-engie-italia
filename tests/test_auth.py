import base64
import hashlib
import time
import unittest
from urllib.parse import parse_qs, urlencode, urlsplit

import jwt
from cryptography.hazmat.primitives.asymmetric import rsa
from test_client import Response, Session

from engie_italia.auth import (
    CALLBACK,
    ISSUER,
    AuthorizationAttempt,
    async_complete_authorization,
)
from engie_italia.errors import (
    AuthenticationError,
    AuthorizationError,
    AuthorizationFailure,
    PayloadError,
    TransportError,
)
from engie_italia.session import SessionTokens


def callback(attempt, **changes):
    return (
        CALLBACK
        + "?"
        + urlencode({"state": attempt.state, "code": "synthetic-code", **changes})
    )


class AuthorizationTests(unittest.IsolatedAsyncioTestCase):
    @classmethod
    def setUpClass(cls):
        cls.key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
        cls.jwk = jwt.algorithms.RSAAlgorithm.to_jwk(cls.key.public_key(), as_dict=True)
        cls.jwk.update(kid="synthetic-key", use="sig", alg="RS256")

    def response(self, attempt, **claims):
        identity = jwt.encode(
            {
                "iss": ISSUER,
                "aud": attempt.client_id,
                "sub": "synthetic-user",
                "nonce": attempt.nonce,
                "exp": int(time.time()) + 300,
                "iat": int(time.time()),
                **claims,
            },
            self.key,
            algorithm="RS256",
            headers={"kid": "synthetic-key"},
        )
        return Response(
            payload={
                "id_token": identity,
                "access_token": "synthetic-access",
                "refresh_token": "synthetic-refresh",
                "expires_in": 3600,
                "token_type": "Bearer",
            }
        )

    async def test_pkce_and_verified_identity(self):
        attempt = AuthorizationAttempt("synthetic-client")
        params = parse_qs(urlsplit(attempt.authorization_url).query)
        challenge = (
            base64.urlsafe_b64encode(hashlib.sha256(attempt.verifier.encode()).digest())
            .decode()
            .rstrip("=")
        )
        self.assertEqual(params["code_challenge"], [challenge])
        self.assertEqual(params["code_challenge_method"], ["S256"])
        session = Session(
            Response(payload={"keys": [self.jwk]}), self.response(attempt)
        )
        account, tokens = await async_complete_authorization(
            session, attempt, callback(attempt)
        )
        self.assertEqual(
            account, hashlib.sha256((ISSUER + "synthetic-user").encode()).hexdigest()
        )
        self.assertEqual(tokens.refresh_token, "synthetic-refresh")
        self.assertEqual(attempt.verifier, "")
        self.assertNotIn("synthetic", repr(tokens))
        self.assertNotIn("synthetic", repr(attempt))
        self.assertFalse(session.calls[1][2]["allow_redirects"])
        with self.assertRaises(AuthenticationError):
            attempt.consume_callback(callback(attempt))

    async def test_untrusted_callbacks_do_not_make_requests(self):
        attempt = AuthorizationAttempt("synthetic-client")
        for value in (
            callback(attempt, state="wrong"),
            callback(attempt) + "&code=second",
            callback(attempt).replace("https:", "http:"),
            callback(attempt).replace("login.engie.it", "example.invalid"),
            callback(attempt) + "#fragment",
            callback(attempt, error="denied"),
            None,
            12,
        ):
            with self.subTest(value=type(value).__name__):
                session = Session()
                with self.assertRaises(AuthenticationError):
                    await async_complete_authorization(session, attempt, value)
                self.assertEqual(session.calls, [])

    async def test_expired_attempt(self):
        attempt = AuthorizationAttempt(
            "synthetic-client", created_at=time.monotonic() - 601
        )
        with self.assertRaises(AuthenticationError):
            attempt.consume_callback(callback(attempt))

    async def test_callback_errors_preserve_the_current_attempt(self):
        attempt = AuthorizationAttempt("synthetic-client")
        link = attempt.authorization_url
        for value, reason in (
            ("https://example.invalid/", AuthorizationFailure.INVALID_CALLBACK),
            (
                callback(attempt, state="other-attempt"),
                AuthorizationFailure.STATE_MISMATCH,
            ),
            (callback(attempt) + "&code=", AuthorizationFailure.INVALID_CALLBACK),
            (callback(attempt) + "&state=", AuthorizationFailure.INVALID_CALLBACK),
            (callback(attempt, error="private-error"), AuthorizationFailure.DENIED),
            ("x" * 8193, AuthorizationFailure.INVALID_CALLBACK),
        ):
            with self.subTest(reason=reason):
                with self.assertRaises(AuthorizationError) as error:
                    attempt.consume_callback(value)
                self.assertEqual(error.exception.reason, reason)
                self.assertEqual(str(error.exception), reason.value)
                self.assertFalse(attempt.consumed)
                self.assertEqual(attempt.authorization_url, link)
        self.assertEqual(attempt.consume_callback(callback(attempt)), "synthetic-code")

    async def test_key_fetch_failure_can_retry_same_authorization(self):
        attempt = AuthorizationAttempt("synthetic-client")
        returned = callback(attempt)
        with self.assertRaises(TransportError):
            await async_complete_authorization(
                Session(TimeoutError()), attempt, returned
            )
        self.assertFalse(attempt.consumed)
        self.assertTrue(attempt.verifier)
        session = Session(
            Response(payload={"keys": [self.jwk]}), self.response(attempt)
        )
        await async_complete_authorization(session, attempt, returned)
        self.assertTrue(attempt.consumed)

    async def test_rejected_code_has_distinct_failure_and_clears_verifier(self):
        attempt = AuthorizationAttempt("synthetic-client")
        session = Session(Response(payload={"keys": [self.jwk]}), Response(403))
        with self.assertRaises(AuthorizationError) as error:
            await async_complete_authorization(session, attempt, callback(attempt))
        self.assertEqual(error.exception.reason, AuthorizationFailure.TOKEN_EXCHANGE)
        self.assertTrue(attempt.consumed)
        self.assertEqual(attempt.verifier, "")

    async def test_uncertain_exchange_is_not_replayed(self):
        attempt = AuthorizationAttempt("synthetic-client")
        session = Session(Response(payload={"keys": [self.jwk]}), TimeoutError())
        with self.assertRaises(TransportError):
            await async_complete_authorization(session, attempt, callback(attempt))
        self.assertTrue(attempt.consumed)
        self.assertEqual(attempt.verifier, "")
        with self.assertRaises(AuthorizationError) as error:
            await async_complete_authorization(Session(), attempt, callback(attempt))
        self.assertEqual(error.exception.reason, AuthorizationFailure.USED)

    async def test_wrong_claims_rejected(self):
        for claims in (
            {"nonce": "wrong"},
            {"iss": "https://example.invalid/"},
            {"aud": "wrong"},
            {"exp": int(time.time()) - 60},
            {"sub": ""},
        ):
            attempt = AuthorizationAttempt("synthetic-client")
            session = Session(
                Response(payload={"keys": [self.jwk]}), self.response(attempt, **claims)
            )
            with self.assertRaises(AuthenticationError):
                await async_complete_authorization(session, attempt, callback(attempt))

    async def test_missing_key_rejected(self):
        attempt = AuthorizationAttempt("synthetic-client")
        session = Session(Response(payload={"keys": []}), self.response(attempt))
        with self.assertRaises(AuthenticationError):
            await async_complete_authorization(session, attempt, callback(attempt))

    async def test_transport_and_payload_errors_sanitized(self):
        for response, exception in (
            (Response(302), TransportError),
            (Response(401), AuthenticationError),
            (Response(raw=b"private-not-json"), PayloadError),
            (Response(raw=b"x" * (1024 * 1024 + 1)), PayloadError),
            (TimeoutError("private"), TransportError),
        ):
            attempt = AuthorizationAttempt("synthetic-client")
            with self.assertRaises(exception) as error:
                await async_complete_authorization(
                    Session(response), attempt, callback(attempt)
                )
            self.assertNotIn("private", str(error.exception))


class SessionTests(unittest.TestCase):
    def test_private_storage_roundtrip(self):
        tokens = SessionTokens(
            "synthetic-access", "synthetic-refresh", time.time() + 300
        )
        self.assertEqual(SessionTokens.from_storage(tokens.as_storage()), tokens)
        self.assertGreater(tokens.remaining_seconds, 290)
        self.assertEqual(SessionTokens("a", "r", 0).remaining_seconds, 1)

    def test_invalid_storage(self):
        for data in (
            None,
            {},
            {"access_token": "a", "refresh_token": "r", "expires_at": float("nan")},
        ):
            with self.assertRaises(ValueError):
                SessionTokens.from_storage(data)
