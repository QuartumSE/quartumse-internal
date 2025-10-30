# CNAME File for GitHub Pages

## Purpose

The `docs/CNAME` file configures the custom domain for GitHub Pages deployment.

**Domain**: quartumse.com

## How It Works

1. MkDocs copies all files from `docs/` to the built site
2. `mkdocs gh-deploy` pushes the built site to the `gh-pages` branch
3. GitHub Pages reads the `CNAME` file and configures the custom domain

## CRITICAL: Do Not Delete

**Problem**: If `CNAME` is missing, GitHub Pages reverts to the default subdomain:
- Default: `https://quartumse.github.io/quartumse/` or random subdomain like `verbose-adventure-l1nqelq.pages.github.io`
- With CNAME: `https://quartumse.com/`

**This file was added because**: Previous deployments deleted a manually-added CNAME from the gh-pages branch. Storing it in `docs/` ensures it's included in every deployment.

## DNS Configuration Required

For the custom domain to work, DNS must be configured at the domain registrar (Namecheap):

### A Records (for root domain quartumse.com)
```
185.199.108.153
185.199.109.153
185.199.110.153
185.199.111.153
```

### CNAME Record (for www redirect)
```
www.quartumse.com → quartumse.github.io
```

### Redirect (optional)
- quartumse.org → quartumse.com (URL redirect at registrar)

## Verification

After DNS propagates (1-48 hours), verify:

```bash
# Check DNS resolution
dig quartumse.com +short

# Check HTTPS
curl -I https://quartumse.com/

# Verify CNAME exists in deployment
curl https://quartumse.com/CNAME
```

## Troubleshooting

**Site shows random subdomain?**
1. Check if `docs/CNAME` exists in master branch
2. Verify `mkdocs gh-deploy` was run after adding CNAME
3. Check GitHub Pages settings: Settings → Pages → Custom domain

**DNS not resolving?**
1. Wait for DNS propagation (up to 48 hours)
2. Verify A records are configured correctly at registrar
3. Use `dig quartumse.com` to check DNS status

## Related Files

- `mkdocs.yml` - MkDocs configuration (includes comment about CNAME)
- `.github/workflows/deploy.yml` - GitHub Pages deployment workflow
- `docs/ops/ci_expansion_guide.md` - CI/CD documentation

## References

- [GitHub Pages Custom Domains](https://docs.github.com/en/pages/configuring-a-custom-domain-for-your-github-pages-site)
- [MkDocs Deployment](https://www.mkdocs.org/user-guide/deploying-your-docs/)
