const express = require('express');
const cheerio = require('cheerio');
const morgan = require('morgan');
const path = require('path');
const { URL } = require('url');

const app = express();
const PORT = parseInt(process.env.PORT || '8080', 10);

app.use(morgan('dev'));
app.use(express.static(path.join(__dirname, 'public')));

function isValidHttpUrl(string) {
  try {
    const url = new URL(string);
    return url.protocol === 'http:' || url.protocol === 'https:';
  } catch (e) {
    return false;
  }
}

function makeAbsoluteUrl(base, relative) {
  try {
    return new URL(relative, base).toString();
  } catch (e) {
    return relative;
  }
}

app.get('/proxy', async (req, res) => {
  const target = req.query.url;
  if (!target || !isValidHttpUrl(target)) {
    return res.status(400).send('Invalid or missing url parameter. Example: /proxy?url=https://example.com');
  }

  try {
    const fetched = await fetch(target, { redirect: 'follow' });
    const contentType = fetched.headers.get('content-type') || '';

    if (contentType.includes('text/html')) {
      const body = await fetched.text();
      const $ = cheerio.load(body, { decodeEntities: false });

      $('[href]').each((i, el) => {
        const orig = $(el).attr('href');
        if (!orig) return;
        const abs = makeAbsoluteUrl(fetched.url, orig);
        if (isValidHttpUrl(abs)) {
          $(el).attr('href', '/proxy?url=' + encodeURIComponent(abs));
        }
      });

      $('[src]').each((i, el) => {
        const orig = $(el).attr('src');
        if (!orig) return;
        const abs = makeAbsoluteUrl(fetched.url, orig);
        if (isValidHttpUrl(abs)) {
          $(el).attr('src', '/proxy?url=' + encodeURIComponent(abs));
        }
      });

      $('form[action]').each((i, el) => {
        const orig = $(el).attr('action');
        if (!orig) return;
        const abs = makeAbsoluteUrl(fetched.url, orig);
        if (isValidHttpUrl(abs)) {
          $(el).attr('action', '/proxy?url=' + encodeURIComponent(abs));
        }
      });

      $('[srcset]').each((i, el) => {
        const orig = $(el).attr('srcset');
        if (!orig) return;
        const parts = orig.split(',').map(p => p.trim()).map(item => {
          const [urlPart, descriptor] = item.split(/\s+/, 2);
          const abs = makeAbsoluteUrl(fetched.url, urlPart);
          if (isValidHttpUrl(abs)) return '/proxy?url=' + encodeURIComponent(abs) + (descriptor ? ' ' + descriptor : '');
          return item;
        });
        $(el).attr('srcset', parts.join(', '));
      });

      // Do NOT inject a <base> tag pointing to the remote origin.
      // Adding a base with the fetched origin would cause rewritten
      // absolute-path links (e.g. '/proxy?url=...') to resolve against
      // the remote host (e.g. https://en.wikipedia.org/proxy?...) instead
      // of this proxy, which breaks navigation from the iframe. We already
      // rewrite links to route through /proxy, so a base tag is unnecessary.

      res.set('content-type', 'text/html; charset=utf-8');
      return res.send($.html());
    }

    res.set('content-type', contentType);
    const stream = fetched.body;
    if (stream) {
      stream.pipe(res);
    } else {
      const buf = await fetched.arrayBuffer();
      res.send(Buffer.from(buf));
    }
  } catch (err) {
    console.error('Proxy error:', err);
    res.status(500).send('Error fetching target: ' + String(err.message || err));
  }
});

app.get('/', (req, res) => {
  res.sendFile(path.join(__dirname, 'public', 'index.html'));
});

app.listen(PORT, () => {
  console.log(`Embedded browser proxy running on http://localhost:${PORT}`);
});
