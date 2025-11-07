## llmosaic-rag (Helm stack)

Umbrella Helm chart for a basic RAG foundation that layers on top of llmosaic-db
and integrates with the LLMosaic LLM API (llmapi) via values.

Contents
- chart/llmosaic-rag — installable Helm chart
- starter/ — values + extras for RAG scenarios

Quick install (from repo)
```
kubectl create ns <tenant-ns> || true
helm upgrade --install llmosaic-rag ./chart/llmosaic-rag \
  -n <tenant-ns> \
  -f ./starter/values.yaml
```

This chart vendors llmosaic-db as a subchart and adds RAG-oriented defaults and
integration values (e.g., llmapi endpoints/secrets) without shipping any secrets.

