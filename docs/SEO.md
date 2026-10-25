# Routes and search discovery

Public pages are Django-rendered HTML enhanced by the TypeScript client. An initial request has a meaningful title, heading, description, product history, disclosed ingredients and links without requiring client rendering. `/catalogue/` lists canonical roots; `/spirits/<slug>/` is the stable product URL. History API navigation, legacy hash migration and local chapter anchors are supported.

Configure `PUBLIC_BASE_URL` to the actual public HTTPS origin. Canonical and Open Graph URLs, Schema.org JSON-LD and `/sitemap.xml` use this trusted setting rather than an incoming Host header. The frontend uses the current origin for metadata while navigating. Only published products are readable or listed in the sitemap; merged aliases permanently redirect to the canonical product. Member pages use noindex, nofollow. `/robots.txt` disallows admin/API/account/setup/studio/shelf and advertises the sitemap. Robots controls are not authorization.

Stable entry names `/assets/app.js` and `/assets/style.css` use no-cache so an HTML response cannot pin an obsolete entry after a rebuild. Dependency chunks are content-hashed and immutable. Publish backend and frontend together; product text changes are reflected server-side without a static page rebuild. The Nginx root location proxies to Django, while images and chunks remain static.

No fake offers, ratings or availability are inserted into structured data. Product identity metadata does not assert a retail listing or guarantee a search-engine rich result. No analytics, external fonts or tracking pixels are installed.
