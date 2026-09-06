aws s3 sync dist/frontend/browser/ \
  s3://salk-colony-manager-frontend/ \
  --delete

aws cloudfront create-invalidation \
  --distribution-id E1ZXHBAO1ZGLCU \
  --paths "/*"