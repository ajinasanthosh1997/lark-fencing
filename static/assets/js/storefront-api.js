document.addEventListener('DOMContentLoaded', async () => {
  const grid = document.querySelector('[data-generated-catalog]');
  if (!grid) return;
  const escape = value => String(value ?? '').replace(/[&<>"']/g, char => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[char]));
  const slug = value => String(value).toLowerCase().replace(/[^a-z0-9]+/g, '-').replace(/^-|-$/g, '');
  try {
    const [productResponse, categoryResponse] = await Promise.all([fetch('/api/v1/products/'), fetch('/api/v1/categories/')]);
    if (!productResponse.ok || !categoryResponse.ok) throw new Error('Catalogue API unavailable');
    const productData = await productResponse.json(), categories = await categoryResponse.json();
    const products = Array.isArray(productData) ? productData : productData.results || [];
    const filters = document.querySelector('.filter-group');
    if (filters) filters.innerHTML = `<button class="filter active" data-api-filter="all">All / ${products.length}</button>${categories.map(category => `<button class="filter" data-api-filter="${category.id}">${escape(category.name)} / ${category.product_count}</button>`).join('')}`;
    const render = list => {
      grid.innerHTML = list.map((product, index) => {
        const query = new URLSearchParams({id: product.slug, name: product.name, category: product.category?.name || 'Fencing', image: product.image_url, description: product.description, meta: product.sku, price: `€${product.price}`});
        return `<article class="product-card" data-api-category="${product.category?.id || ''}" data-api-search="${escape(`${product.name} ${product.description} ${product.category?.name || ''}`.toLowerCase())}"><a href="/product-detail.html?${query}"><div class="product-stage product-photo-stage"><span class="tag">${escape(product.category?.name || 'Fencing')}</span><img src="${escape(product.image_url)}" alt="${escape(product.name)}" loading="${index < 6 ? 'eager' : 'lazy'}"></div><div class="product-info"><div><p>${escape(product.sku)}</p><h2>${escape(product.name)}</h2></div><strong>€${escape(product.price)}</strong><span>${escape(product.description)}</span></div></a></article>`;
      }).join('');
    };
    render(products);
    let category = 'all';
    const search = document.querySelector('#catalog-search');
    const apply = () => {
      const term = (search?.value || '').trim().toLowerCase();
      [...grid.children].forEach(card => card.hidden = !((category === 'all' || card.dataset.apiCategory === category) && card.dataset.apiSearch.includes(term)));
    };
    filters?.querySelectorAll('[data-api-filter]').forEach(button => button.addEventListener('click', () => {
      filters.querySelectorAll('.filter').forEach(item => item.classList.toggle('active', item === button)); category = button.dataset.apiFilter; apply();
    }));
    search?.addEventListener('input', apply);
  } catch (error) {
    console.error('Could not load the dynamic catalogue:', error);
  }
});
