# Youtube playlist diff

## Deploy

```
$ npm install && npx clasp create && npm run deploy
```

## Issues

- Directory is a mess, but Apps Sript and clasp has issue handling source in subfolders.
- Better to use json schema / json typedef to generate code instead of hand craft db schema, A LOT scripting required.
- source need to be prefixed for script loading order, and it maybe break at any time.
- When deploy this script first time, `appsscript.json` is pushed but service declared is not actually enabled. Manual remove-then-add services is required.
- Trigger setup is not automated.
