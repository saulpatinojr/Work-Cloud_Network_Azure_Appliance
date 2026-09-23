"""
Probe the AI Foundry path from inside the Container Apps environment.

210-deploy runs this as a one-off Container Apps Job in the same environment,
with the same user-assigned identity and the same api image as cna-api
("Verify the AI Foundry path from inside the environment", saas only). It
answers the two questions the deployment manifest used to leave as `required`
markers that nothing ever flipped (TODO.md → T-104):

  FOUNDRY_DNS        does the Foundry account's host name resolve, from inside
                     the VNet, to an address in the private-endpoint subnet?
                     (private DNS zone linked, A record present — not the
                     public front end, which the account refuses anyway)
  FOUNDRY_INFERENCE  does one chat completion against the configured deployment
                     succeed with a managed-identity token — the exact call
                     path cna-api's azure-openai engine uses (DefaultAzureCredential
                     bearer token, httpx POST, max_completion_tokens)?

Each result is printed as KEY=passed|failed so the workflow can read it back
from the job's console log; the exit status is 0 only when both pass.

Configuration comes from the job's environment:
  AZURE_OPENAI_ENDPOINT, AZURE_OPENAI_DEPLOYMENT, AZURE_OPENAI_API_VERSION
      copied from the running api container app, so the probe tests what the
      app is actually configured with;
  AZURE_CLIENT_ID     the user-assigned identity (DefaultAzureCredential picks
                      it up in a Container Apps Job);
  CNA_PRIVATE_ENDPOINT_SUBNET_PREFIX  the subnet the private endpoints live in.

Nothing here is secret: the token is requested and used in-process, never
printed, and the model is asked for a single word.
"""

from __future__ import annotations

import ipaddress
import os
import socket
import sys
from urllib.parse import urlparse

TOKEN_SCOPE = "https://cognitiveservices.azure.com/.default"
REQUEST_TIMEOUT_SECONDS = 60
# Reasoning-class deployments reject very small budgets; 16 is the documented floor.
MAX_COMPLETION_TOKENS = 16


def check_dns(host: str, subnet_prefix: str) -> bool:
    try:
        addresses = sorted({info[4][0] for info in socket.getaddrinfo(host, 443, proto=socket.IPPROTO_TCP)})
    except socket.gaierror as exc:
        print(f"dns: {host} does not resolve from inside the environment: {exc}")
        return False
    network = ipaddress.ip_network(subnet_prefix, strict=False)
    inside = [a for a in addresses if ipaddress.ip_address(a) in network]
    print(f"dns: {host} -> {addresses} (private-endpoint subnet {network})")
    if not inside:
        print(
            "dns: no address falls inside the private-endpoint subnet — the private DNS zone is "
            "not linked to the VNet or the record is missing, so traffic would go to the public "
            "front end, which this account refuses (public_network_access_enabled = false)."
        )
        return False
    return True


def check_inference(endpoint: str, deployment: str, api_version: str) -> bool:
    import httpx
    from azure.identity import DefaultAzureCredential

    token = DefaultAzureCredential().get_token(TOKEN_SCOPE)
    url = f"{endpoint.rstrip('/')}/openai/deployments/{deployment}/chat/completions?api-version={api_version}"
    response = httpx.post(
        url,
        headers={"Content-Type": "application/json", "Authorization": f"Bearer {token.token}"},
        json={
            "messages": [{"role": "user", "content": "Reply with the single word: pong"}],
            "max_completion_tokens": MAX_COMPLETION_TOKENS,
        },
        timeout=REQUEST_TIMEOUT_SECONDS,
    )
    if response.status_code >= 400:
        print(f"inference: HTTP {response.status_code} from {deployment}: {response.text[:400]}")
        return False
    data = response.json()
    choices = data.get("choices") or []
    print(
        f"inference: deployment {deployment} answered "
        f"(model {data.get('model', '?')}, {len(choices)} choice(s), "
        f"{(data.get('usage') or {}).get('total_tokens', '?')} tokens)"
    )
    return bool(choices)


def main() -> int:
    endpoint = os.environ.get("AZURE_OPENAI_ENDPOINT", "").strip()
    deployment = os.environ.get("AZURE_OPENAI_DEPLOYMENT", "").strip()
    api_version = os.environ.get("AZURE_OPENAI_API_VERSION", "").strip()
    subnet_prefix = os.environ.get("CNA_PRIVATE_ENDPOINT_SUBNET_PREFIX", "").strip()

    results = {"FOUNDRY_DNS": "failed", "FOUNDRY_INFERENCE": "failed"}
    missing = [
        name
        for name, value in (
            ("AZURE_OPENAI_ENDPOINT", endpoint),
            ("AZURE_OPENAI_DEPLOYMENT", deployment),
            ("AZURE_OPENAI_API_VERSION", api_version),
            ("CNA_PRIVATE_ENDPOINT_SUBNET_PREFIX", subnet_prefix),
        )
        if not value
    ]
    if missing:
        print(f"probe: not configured — missing {', '.join(missing)}; the api container app is not wired for saas.")
    else:
        host = urlparse(endpoint).hostname or endpoint
        try:
            if check_dns(host, subnet_prefix):
                results["FOUNDRY_DNS"] = "passed"
        except Exception as exc:  # noqa: BLE001 — a probe reports, it never crashes silently
            print(f"dns: probe error: {type(exc).__name__}: {exc}")
        try:
            if check_inference(endpoint, deployment, api_version):
                results["FOUNDRY_INFERENCE"] = "passed"
        except Exception as exc:  # noqa: BLE001
            print(f"inference: probe error: {type(exc).__name__}: {exc}")

    for key, value in results.items():
        print(f"{key}={value}")
    return 0 if all(v == "passed" for v in results.values()) else 1


if __name__ == "__main__":
    sys.exit(main())
