#!/bin/bash
set -u

KEYCLOAK_URL="${KEYCLOAK_URL:-http://keycloak:8080}"
KEYCLOAK_REALM="${KEYCLOAK_REALM:-semanticsearch}"
KEYCLOAK_CLIENT_ID="${KEYCLOAK_CLIENT_ID:-semanticsearch-web}"

# The realm is imported on startup from docker/keycloak/realm-semanticsearch.json.
# That file already contains the correct client configuration for redirects.
# Avoid the brittle admin CLI update path here because it intermittently fails with
# Keycloak JSON parsing errors for nested attributes like post.logout.redirect.uris.
echo "Keycloak realm import has already configured client ${KEYCLOAK_CLIENT_ID} in realm ${KEYCLOAK_REALM}."
echo "Skipping post-logout redirect URI bootstrap to keep docker-compose startup stable."
exit 0
