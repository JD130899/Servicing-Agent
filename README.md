# Servicing Agent: Kubernetes demo

A separate deployment copy of your project. The original ZIP is unchanged.
This package contains no credentials, private keys, virtual environment, or Salesforce CLI login.

## What changed

- One Python image, run as two containers in one pod: FastAPI and MCP.
- MCP remains bound to localhost:8002. Containers in this pod share localhost.
- FastAPI listens on 0.0.0.0:8000 and adds /healthz and /readyz.
- Salesforce supports token and JWT authentication; your original CLI mode remains the default for local use.
- Snowflake's private key path and role can be configured through environment variables.
- Saved Cohere index is included. No ingestion, PDF downloads, or parsing runs at startup.
- Removed the obsolete OpenAI retrieval definitions from document_search.py; Cohere retrieval is preserved.
- The Kubernetes Service is private. Use port-forward for this demo.

## First: build the image on your Mac

Open Docker Desktop and wait for it to start. Extract this package into a NEW folder.
In a terminal, change into that folder, which contains Dockerfile:

```sh
docker version
docker build -t servicing-agent:v1 .
```

Dependencies are pinned to the direct package versions found in your uploaded environment.
Transitive dependencies are not locked. A successful Linux image build is still required;
it could not be run in the preparation environment, which has no Docker executable.
Ingestion scripts are supplied for reference but are not in the runtime image.
If you run ingestion separately, install requirements-rag.txt and google-cloud-storage too.

## Credentials on your Mac (never paste the values into chat)

Copy .env.example to .env. Fill OpenAI, Cohere, and Snowflake values from your original
local .env. Use plain KEY=value lines without quotes or export prefixes: kubectl's
--from-env-file treats quotes literally. Copy your original snowflake_key.p8 into this
NEW folder. It is excluded from the image and git.

For the initial demo, use your existing Mac Salesforce login to export a temporary token.
Run this script with the Python interpreter in your ORIGINAL project's virtual environment,
or another environment with simple-salesforce and python-dotenv installed:

```sh
python export_salesforce_token.py
```

The sf executable and servicing-demo CLI login must be available on that Mac.
The script writes only the Salesforce fields into the new .env without printing credentials.
This token expires/revokes and is NOT a permanent authentication solution.
Do not copy Salesforce CLI state into the container.

## Choose your Kubernetes environment

These commands assume kubectl is already pointing to the intended cluster.
Check `kubectl config current-context` before making changes.
For local practice, a kind cluster can use the locally built image:

```sh
kind create cluster --name servicing-demo
kind load docker-image servicing-agent:v1 --name servicing-demo
```

If you already have that kind cluster, skip creation.
Local Kubernetes avoids Google hosting costs. Docker Desktop and kind must be installed first.
For GKE, the image must instead be built for the node architecture (usually linux/amd64),
pushed to a private registry and BOTH image fields in kubernetes.yaml replaced with its
registry URL. Configure node image-pull permissions. Cloud cluster creation/billing and
registry provisioning are separate steps; no cloud resources have been created by this package.

## Deploy into your selected cluster

From this package's folder:

```sh
kubectl create namespace servicing-demo
kubectl -n servicing-demo create secret generic servicing-env --from-env-file=.env
kubectl -n servicing-demo create secret generic servicing-keys --from-file=snowflake_key.p8
kubectl -n servicing-demo apply -f kubernetes.yaml
kubectl -n servicing-demo rollout status deployment/servicing-agent --timeout=300s
kubectl -n servicing-demo port-forward service/servicing-agent 8080:80
```

Skip namespace creation if it already exists. Commands above initially create secrets;
if they already exist, update them using your cluster's normal secret-management process.
Open http://127.0.0.1:8080 and keep port-forward running. Do not expose port 8002 publicly.
If refreshing a Salesforce token, update servicing-env and restart the Deployment:
`kubectl -n servicing-demo rollout restart deployment/servicing-agent`.
Changing the local .env alone does not update Kubernetes.

## Verify actual behavior

- UI opens; /healthz and /readyz return 200.
- Ask for the fictional account balance; compare with Snowflake.
- Ask support hours; check PDF citation and answer.
- Request one explicitly labeled demo Case, record its ID, then look it up.
  This creates a real Case in your demo Salesforce org. Do not automatically repeat on timeout.
- Restart the Deployment and repeat read-only checks to verify secrets and index survive replacement.

Read logs locally if troubleshooting; redact credentials and customer data before sharing:

```sh
kubectl -n servicing-demo get pods
kubectl -n servicing-demo logs deployment/servicing-agent -c web
kubectl -n servicing-demo logs deployment/servicing-agent -c tools
```

Readiness checks only web/MCP startup connectivity, not Salesforce, Snowflake or model APIs.
Probe success is not end-to-end validation.

## Salesforce JWT mode for longer-lived deployment

The client supports:

```
SALESFORCE_AUTH_MODE=jwt
SALESFORCE_USERNAME=your-authorized-integration-user
SALESFORCE_CONSUMER_KEY=your-app-consumer-key
SALESFORCE_DOMAIN=login
```

Configure a Salesforce OAuth app that allows JWT bearer authentication, register its public
certificate, and authorize the integration user. App availability and administrator permissions
vary by org. Use a SEPARATE Salesforce private key; do not reuse the Snowflake key.
Mount it by recreating/updating servicing-keys with BOTH snowflake_key.p8 and salesforce.key.
The manifest sets SALESFORCE_PRIVATE_KEY_FILE=/run/secrets/salesforce.key.
Use domain=test for a sandbox, where appropriate.
No JWT app or Salesforce permissions were created by this package.

## Limits before public production

This is a privately accessed Kubernetes DEMO. It has no customer login, per-customer record
permissions, request rate limiting, durable chat history, write idempotency, or centralized
tracing. Snowflake defaults to your existing ACCOUNTADMIN role; replace it with a role limited
to required reads. Kubernetes Secrets require suitable RBAC and encryption configuration;
for cloud production use an appropriate managed secret integration. Public use also needs
HTTPS and authentication. Replicas remain 1; automatic scaling is not configured.

## Cleanup

`kubectl -n servicing-demo delete -f kubernetes.yaml` removes this Deployment and Service,
but not namespace or secrets. For the dedicated local kind cluster only:
`kind delete cluster --name servicing-demo` removes that entire local cluster.
For cloud resources, deleting this workload does not delete the GKE cluster, disks or registry
and does not guarantee billing stops.

References:
- https://kubernetes.io/docs/concepts/workloads/pods/
- https://kubernetes.io/docs/tasks/access-application-cluster/port-forward-access-application-cluster/
- https://github.com/simple-salesforce/simple-salesforce/blob/master/docs/user_guide/examples.rst
